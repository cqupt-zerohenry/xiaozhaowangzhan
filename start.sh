#!/usr/bin/env bash
set -e

# ===================================================================
#  一键启动脚本 —— pnpm dev 调用此脚本
#  自动完成：依赖检测 → MySQL/Redis 启动 → 建库 → 后端 → 前端
# ===================================================================

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.logs"
COMPOSE_FILE="$ROOT_DIR/docker-compose.dev.yml"

# ---------- 工具函数 ----------
say()  { printf "\033[1;32m▸ %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m⚠ %s\033[0m\n" "$*"; }
fail() { printf "\033[1;31m✖ %s\033[0m\n" "$*"; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

is_port_listening() {
  local port="$1"
  if command_exists lsof; then
    lsof -ti tcp:"$port" -sTCP:LISTEN >/dev/null 2>&1; return $?
  fi
  if command_exists ss; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":$port$"; return $?
  fi
  return 1
}

wait_for_port() {
  local port="$1" name="$2" retries="${3:-30}" i=0
  while [ "$i" -lt "$retries" ]; do
    is_port_listening "$port" && return 0
    i=$((i + 1)); sleep 1
  done
  fail "$name 未能在端口 $port 上启动（超时 ${retries}s）"
}

find_pids_by_port() {
  local port="$1"
  if command_exists lsof; then
    lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true
  fi
}

kill_port() {
  local port="$1"
  local pids
  pids=$(find_pids_by_port "$port")
  [ -z "$pids" ] && return 0
  for pid in $pids; do
    [ "$pid" -gt 0 ] 2>/dev/null && kill "$pid" 2>/dev/null || true
  done
  sleep 1
  for pid in $pids; do
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  done
}

# ---------- 1. 系统依赖检测与安装 ----------
say "检查系统依赖..."

# Python3
if ! command_exists python3; then
  if command_exists brew; then brew install python; else fail "缺少 python3，请先安装"; fi
fi
PYTHON3=$(command -v python3)
say "Python3: $($PYTHON3 --version)"

# Node.js
if ! command_exists node; then
  if command_exists brew; then brew install node; else fail "缺少 Node.js，请先安装"; fi
fi
say "Node: $(node --version)"

# pnpm
if ! command_exists pnpm; then
  say "安装 pnpm..."
  npm install -g pnpm 2>/dev/null || corepack enable pnpm 2>/dev/null || fail "无法安装 pnpm"
fi
say "pnpm: $(pnpm --version)"

mkdir -p "$LOG_DIR"

# ---------- 2. MySQL + Redis 基础设施 ----------
say "检查 MySQL / Redis..."

start_infra() {
  local mysql_ok=0 redis_ok=0
  is_port_listening 3306 && mysql_ok=1
  is_port_listening 6379 && redis_ok=1

  if [ "$mysql_ok" -eq 1 ] && [ "$redis_ok" -eq 1 ]; then
    say "MySQL(3306) 和 Redis(6379) 已在运行"
    return 0
  fi

  # 优先 Docker Compose
  if [ -f "$COMPOSE_FILE" ] && command_exists docker && docker info >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      say "使用 Docker Compose 启动 MySQL/Redis..."
      docker compose -f "$COMPOSE_FILE" up -d mysql redis
      wait_for_port 3306 "MySQL" 60
      wait_for_port 6379 "Redis" 30
      say "MySQL/Redis 已通过 Docker 启动"
      return 0
    fi
  fi

  # macOS brew services
  if command_exists brew; then
    [ "$mysql_ok" -eq 0 ] && { say "brew services start mysql"; brew services start mysql >/dev/null 2>&1 || true; }
    [ "$redis_ok" -eq 0 ] && { say "brew services start redis"; brew services start redis >/dev/null 2>&1 || true; }
    wait_for_port 3306 "MySQL" 60
    wait_for_port 6379 "Redis" 30
    say "MySQL/Redis 已通过 brew services 启动"
    return 0
  fi

  fail "无法自动启动 MySQL/Redis。请安装 Docker 或手动启动。"
}

start_infra

# ---------- 3. 确保数据库存在 ----------
ensure_database() {
  say "检查数据库 campus_recruit..."
  # 尝试用 mysql 客户端建库（Docker 或本地均可）
  if command_exists mysql; then
    mysql -u root -proot -h 127.0.0.1 -e "CREATE DATABASE IF NOT EXISTS campus_recruit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null && return 0
  fi
  # Docker exec 方式
  if command_exists docker && docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'campus-mysql'; then
    docker exec campus-mysql mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS campus_recruit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null && return 0
  fi
  warn "无法确认数据库是否存在，如首次运行请确保 campus_recruit 库已创建"
}

ensure_database

# ---------- 4. 后端依赖 ----------
say "准备后端环境..."

if [ ! -d "$BACKEND_DIR/.venv" ] || [ ! -f "$BACKEND_DIR/.venv/bin/pip" ]; then
  say "创建 Python 虚拟环境..."
  rm -rf "$BACKEND_DIR/.venv"
  $PYTHON3 -m venv "$BACKEND_DIR/.venv"
fi

# 确保 venv 的 python 链接正确
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
VENV_PIP="$BACKEND_DIR/.venv/bin/pip"
if [ ! -x "$VENV_PYTHON" ]; then
  say "修复虚拟环境 python 链接..."
  rm -rf "$BACKEND_DIR/.venv"
  $PYTHON3 -m venv "$BACKEND_DIR/.venv"
fi

say "安装后端依赖..."
"$VENV_PIP" install --quiet --disable-pip-version-check -r "$BACKEND_DIR/requirements.txt"

# ---------- 5. 前端依赖 ----------
say "准备前端环境..."

if [ ! -d "$FRONTEND_DIR/node_modules/.bin" ] || [ ! -x "$FRONTEND_DIR/node_modules/.bin/vite" ]; then
  say "安装前端依赖..."
  (cd "$FRONTEND_DIR" && pnpm install)
fi

# ---------- 6. 释放端口并启动 ----------
kill_port 8000
kill_port 5173

say "启动后端 (FastAPI) → http://localhost:8000"
(cd "$BACKEND_DIR" && "$BACKEND_DIR/.venv/bin/uvicorn" app.main:app \
  --reload --host 0.0.0.0 --port 8000 \
  > "$LOG_DIR/backend.log" 2>&1) &
BACKEND_PID=$!

say "启动前端 (Vite)   → http://localhost:5173"
(cd "$FRONTEND_DIR" && npx vite --host 0.0.0.0 --port 5173 \
  > "$LOG_DIR/frontend.log" 2>&1) &
FRONTEND_PID=$!

# ---------- 7. 打印信息 ----------
echo ""
say "===================== 启动完成 ====================="
echo ""
echo "  前端地址:  http://localhost:5173"
echo "  后端地址:  http://localhost:8000"
echo "  API 文档:  http://localhost:8000/docs"
echo ""
echo "  ┌──────────┬─────────────────────┬──────────┐"
echo "  │   角色   │       邮箱          │   密码   │"
echo "  ├──────────┼─────────────────────┼──────────┤"
echo "  │  管理员  │  admin@test.com     │  123456  │"
echo "  │  企业    │  company@test.com   │  123456  │"
echo "  │  学生    │  student@test.com   │  123456  │"
echo "  └──────────┴─────────────────────┴──────────┘"
echo ""
echo "  日志: $LOG_DIR/backend.log | $LOG_DIR/frontend.log"
echo "  按 Ctrl+C 停止所有服务"
echo ""
say "===================================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; echo ''; say '已停止所有服务'" INT TERM
wait

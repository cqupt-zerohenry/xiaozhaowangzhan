#!/usr/bin/env bash
# 重置数据库（删除所有表后重新启动会自动 seed）
set -e

say() { printf "\033[1;33m▸ %s\033[0m\n" "$*"; }

say "重置数据库 campus_recruit..."

if command -v mysql >/dev/null 2>&1; then
  mysql -u root -proot -h 127.0.0.1 -e "DROP DATABASE IF EXISTS campus_recruit; CREATE DATABASE campus_recruit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'campus-mysql'; then
  docker exec campus-mysql mysql -u root -proot -e "DROP DATABASE IF EXISTS campus_recruit; CREATE DATABASE campus_recruit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
else
  say "无法连接 MySQL，请手动删除 campus_recruit 数据库"
  exit 1
fi

say "数据库已重置，启动后会自动填充默认数据"

# AI Campus Recruit Platform

一个面向校园招聘场景的 AI 驱动招聘平台，连接学生、企业和校方管理员三类角色，覆盖岗位发布、简历管理、投递流程、消息沟通、通知中心、数据统计，以及 AI 岗位推荐、RAG 求职助手、AI 面试等能力。

## 1. 项目概览

### 1.1 技术栈

- 前端：Vue 3 + Vue Router + Vite
- 后端：FastAPI + SQLAlchemy + Pydantic
- 数据库：MySQL 8
- 缓存：Redis 7
- 鉴权：JWT + RBAC
- AI 能力：
  - OpenAI 兼容大模型接口
  - 本地 `sentence-transformers` 向量模型
  - 基于向量检索 + TF-IDF 的混合 RAG
- 文件存储：本地文件系统，默认挂载为 `/uploads`

### 1.2 项目目标

平台核心目标是把校园招聘从“信息展示系统”升级为“招聘流程 + AI 辅助决策系统”，具体包括：

- 为学生提供岗位浏览、个性化推荐、简历管理、投递追踪和模拟面试
- 为企业提供企业主页、岗位发布、候选人查看、在线沟通和 AI 初筛
- 为管理员提供企业审核、公告发布、统计分析和平台治理能力

### 1.3 默认演示账号

项目首次启动时会自动建表并写入演示数据，可直接使用以下账号体验：

| 角色 | 邮箱 | 密码 |
| --- | --- | --- |
| 管理员 | `admin@test.com` | `123456` |
| 企业 | `company@test.com` | `123456` |
| 学生 | `student@test.com` | `123456` |

## 2. 架构说明

### 2.1 总体架构

```text
+-----------------------+
| Vue 3 Web Frontend    |
| Pages / Router / API  |
+----------+------------+
           |
           | HTTP / WS
           v
+-----------------------+
| FastAPI Backend       |
| Routers / RBAC / AI   |
+-----+-----------+-----+
      |           |
      |           +-----------------------------+
      |                                         |
      v                                         v
+-------------+                        +----------------------+
| MySQL       |                        | Redis                |
| 业务数据持久化 |                        | 缓存/计数/加速        |
+-------------+                        +----------------------+
      |
      v
+----------------------+      +----------------------------------+
| 本地文件存储 /uploads |      | AI Services                      |
| 简历/附件/知识库文件   |      | LLM 接口 + Embedding + RAG 检索 |
+----------------------+      +----------------------------------+
```

### 2.2 前端架构

前端位于 `frontend/`，是典型的单页应用：

- 路由层：`src/router.js`
  - 负责页面路由和基于角色的访问控制
  - 区分公开页面、登录后页面和按角色受限页面
- 状态层：`src/store/auth.js`
  - 用 `localStorage` 持久化用户信息和 JWT Token
- 接口层：`src/services/api.js`
  - 统一封装后端请求
  - 默认访问 `/api`
- 页面层：`src/pages/*.vue`
  - 按业务模块拆分页面，例如职位、消息、AI 助手、管理中心等

开发环境下，Vite 通过代理把 `/api`、`/ws`、`/uploads` 转发到 `http://localhost:8000`。

### 2.3 后端架构

后端位于 `backend/`，采用 FastAPI 模块化路由组织：

- 入口：`backend/app/main.py`
  - 注册中间件、异常处理、WebSocket、静态文件、路由
- 配置：`backend/app/config.py`
  - 通过 `.env` 管理数据库、Redis、JWT、LLM、RAG 参数
- 数据访问：`backend/app/db.py`
  - SQLAlchemy Engine / Session / 自动建表
- 数据模型：`backend/app/models.py`
  - 用户、学生、企业、岗位、投递、消息、通知、知识库、AI 面试等实体
- 路由层：`backend/app/routers/*.py`
  - `auth`、`users`、`students`、`companies`
  - `jobs`、`applications`、`messages`、`notifications`
  - `admin`、`favorites`、`files`、`ai`
- 安全能力：
  - JWT 登录态
  - RBAC 角色控制
  - 接口限流
  - JSON 请求 XSS 清洗
  - 全局异常处理

### 2.4 AI 架构

AI 功能由三部分组成：

1. `llm_service.py`
   负责调用 OpenAI 兼容接口。可配置为 OpenAI、DeepSeek、Moonshot 等兼容服务。
2. `rag_service.py`
   负责文本切块、向量化、TF-IDF 召回和混合检索。
3. `job_indexer.py`
   自动把岗位信息写入系统知识库，为 AI 求职助手提供检索上下文。

设计上有两个重要特性：

- 未配置 `LLM_API_KEY` 时，部分 AI 功能仍可通过规则算法降级运行，不会导致系统完全不可用
- 本地 Embedding 模型首次使用时会自动下载，避免所有 AI 能力都依赖外部大模型

## 3. 功能说明

### 3.1 学生端

- 登录与注册
- 个人档案维护
- 求职意向维护
- 在线简历与多版本简历管理
- 岗位列表、职位详情、相似岗位推荐
- 岗位收藏与浏览历史
- 岗位投递与投递状态跟踪
- 与企业在线消息沟通
- 通知中心
- AI 岗位推荐 / 岗位匹配
- AI 求职问答与 RAG 职业助手
- AI 模拟面试
- 面试流程式问答
- 简历解析与简历优化

### 3.2 企业端

- 企业注册与资料维护
- 企业认证提交流程
- 岗位发布、编辑、删除
- 查看投递候选人
- 与学生在线沟通
- 发起学生信息核验请求
- 查看候选人推荐结果
- 创建 AI 面试模板
- AI 初筛面试
- AI 面试会话管理

### 3.3 管理员端

- 企业审核与用户状态管理
- 公告发布和平台消息广播
- 审核记录管理
- 推荐配置管理
- 平台统计与增强统计
- 就业分析与运营分析
- 重置用户密码
- 核验请求审批

### 3.4 实时与附件能力

- WebSocket 在线状态和即时聊天：`/ws/chat/{user_id}`
- 附件上传：`/api/files/upload`
- 静态文件访问：`/uploads/*`

## 4. 目录结构

```text
xiaozhaowangzhan-main/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 应用入口
│   │   ├── models.py         # 数据模型
│   │   ├── routers/          # 业务路由
│   │   ├── llm_service.py    # 大模型调用
│   │   ├── rag_service.py    # RAG 检索
│   │   ├── job_indexer.py    # 岗位知识库索引
│   │   └── seed.py           # 演示数据
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Vue 3 前端
│   ├── src/pages/            # 页面
│   ├── src/services/api.js   # API 封装
│   ├── src/store/auth.js     # 登录状态
│   └── vite.config.js
├── docker-compose.dev.yml    # 开发环境 MySQL/Redis
├── start.sh                  # 一键启动脚本
├── reset-db.sh               # 重置数据库脚本
└── README.md
```

## 5. 开发环境要求

建议准备以下运行环境：

- Python 3
- Node.js
- pnpm
- MySQL 8
- Redis 7
- Docker Desktop 或本地 MySQL/Redis 服务

说明：

- 根目录 `pnpm dev` 会优先使用 `docker compose` 启动 MySQL 和 Redis
- 如果本机没有 Docker，但安装了 Homebrew，也会尝试使用 `brew services` 启动 MySQL/Redis

## 6. 快速启动

### 6.1 一键启动

在项目根目录执行：

```bash
pnpm dev
```

该命令会自动完成以下步骤：

- 检查 Python、Node、pnpm
- 启动 MySQL 和 Redis
- 创建数据库 `campus_recruit`
- 创建后端虚拟环境并安装依赖
- 安装前端依赖
- 启动后端 `http://localhost:8000`
- 启动前端 `http://localhost:5173`

启动后可访问：

- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`

### 6.2 仅启动基础设施

```bash
pnpm infra:up
```

停止基础设施：

```bash
pnpm infra:down
```

## 7. 手动构建与运行

### 7.1 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端特点：

- 启动时自动建表
- 数据库为空时自动写入演示数据
- `/docs` 自动生成接口文档

### 7.2 前端

```bash
cd frontend
pnpm install
pnpm dev
```

前端默认通过 Vite 代理访问本地后端。如果前后端分离部署，需要设置：

```bash
VITE_API_BASE=/api
```

或者改成完整后端地址，例如：

```bash
VITE_API_BASE=https://your-domain.com/api
```

## 8. 构建说明

### 8.1 前端构建

生产构建命令：

```bash
cd frontend
pnpm build
```

构建产物默认输出到：

```text
frontend/dist/
```

可使用以下命令本地预览：

```bash
pnpm preview
```

### 8.2 后端构建

后端是 Python 服务，没有单独的编译产物，通常以以下方式部署：

- Python 虚拟环境 + `uvicorn`
- `gunicorn` + `uvicorn.workers.UvicornWorker`
- 容器镜像

当前仓库没有提供完整生产 Dockerfile，现有 `docker-compose.dev.yml` 仅用于开发阶段启动 MySQL 和 Redis。

## 9. 环境变量

后端核心环境变量在 `backend/.env` 中配置，示例见 `backend/.env.example`。

### 9.1 必填或常用项

```env
APP_NAME=AI Campus Recruit Platform
CORS_ORIGINS=*
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/campus_recruit?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET_KEY=please-change-this-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RAG_CHUNK_SIZE=400
RAG_CHUNK_OVERLAP=80
RAG_TOP_K=5
```

### 9.2 生产环境建议

- `JWT_SECRET_KEY` 必须改为强随机值
- `CORS_ORIGINS` 不要使用 `*`，改为实际域名
- `DATABASE_URL` 使用生产库账号，不要继续使用 `root/root`
- `LLM_API_KEY` 按所选模型服务商配置
- 如不需要公网访问上传文件，应通过 Nginx 或对象存储做访问控制

## 10. 部署说明

### 10.1 推荐部署拓扑

推荐单机部署结构如下：

```text
Nginx
├── /           -> frontend/dist
├── /api        -> 127.0.0.1:8000
├── /ws         -> 127.0.0.1:8000
└── /uploads    -> 127.0.0.1:8000/uploads

FastAPI/Uvicorn -> MySQL
                -> Redis
```

### 10.2 部署步骤

#### 第一步：准备服务器

- 安装 Python 3、Node.js、pnpm
- 安装 MySQL 8、Redis 7、Nginx
- 创建数据库 `campus_recruit`
- 放行 80/443 端口

#### 第二步：部署后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

生产环境建议改为守护方式运行，例如：

```bash
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

或者使用 `systemd` / `supervisor` 托管。

#### 第三步：构建并部署前端

```bash
cd frontend
pnpm install
pnpm build
```

把 `frontend/dist` 发布到 Nginx 静态目录。

#### 第四步：配置 Nginx 反向代理

示例配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/ai-campus-recruit/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 10.3 数据与文件持久化

部署时至少需要持久化以下内容：

- MySQL 数据目录
- Redis 数据目录
- `backend/app/uploads/` 上传文件目录

如果使用容器化部署，也需要把这些目录挂载到宿主机卷。

### 10.4 AI 能力部署注意事项

- 第一次触发 Embedding 时会下载本地模型，需保证服务器能联网，或提前预热
- 若配置了外部 LLM 服务，服务器需能访问对应 API 地址
- 未配置 `LLM_API_KEY` 时，推荐类和评分类功能仍可部分使用，但生成式回答质量会下降

## 11. 测试与验证

后端提供了基础测试：

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

建议上线前至少验证以下内容：

- 三类角色均可登录
- 岗位发布、投递、消息、通知流程正常
- WebSocket 聊天可正常连接
- 文件上传与访问可用
- AI 接口在有无 `LLM_API_KEY` 两种情况下都能按预期运行

## 12. 已知边界与部署建议

- 当前仓库提供的是“开发友好型”启动方案，生产环境仍建议补充 `systemd`、日志轮转、HTTPS、备份与监控
- 当前只提供了开发用 `docker-compose.dev.yml`，未提供完整生产容器编排
- 上传文件默认存在应用本地目录，生产环境更建议迁移到对象存储或共享存储
- 若面向公网开放，建议增加更严格的 CORS、限流、审计和登录安全策略

## 13. 常用命令

```bash
# 根目录一键启动
pnpm dev

# 启动 MySQL / Redis
pnpm infra:up

# 停止 MySQL / Redis
pnpm infra:down

# 重置数据库并重启
pnpm dev:reset

# 运行后端测试
cd backend && pytest

# 构建前端
cd frontend && pnpm build
```


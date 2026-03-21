# Backend (FastAPI)

## Stack

- FastAPI
- MySQL (SQLAlchemy + PyMySQL)
- Redis (cache)
- JWT + RBAC
- BCrypt password hash

## Run All (Root)

```bash
pnpm dev
```

`pnpm dev` will also ensure MySQL (`3306`) and Redis (`6379`) are running.
It prefers Docker Compose (`docker-compose.dev.yml`) and falls back to `brew services`.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# copy env and set MySQL/Redis connection
cp .env.example .env
# create database first (example)
# mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS campus_recruit DEFAULT CHARACTER SET utf8mb4;"
uvicorn app.main:app --reload --port 8000
```

## Evaluate Recommendation

```bash
python scripts/evaluate_recommendation.py
```

The report will be written to `backend/reports/recommendation_eval_report.md`.

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Endpoints

- `GET /health`
- `POST /api/users` / `POST /api/users/login`
- `GET /api/companies`
- `GET /api/jobs`
- `POST /api/ai/job-match`
- `POST /api/ai/rag`
- `POST /api/ai/interview`
- `POST /api/ai/mock-interview`
- `WS /ws/chat/{user_id}`

from __future__ import annotations

import json
import logging
import os

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.cache import get_redis
from app.config import settings
from app.db import SessionLocal, init_db
from app.routers import ai, admin, applications, auth, companies, favorites, files, jobs, messages, notifications, students, users
from app.seed import seed_data

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=['60/minute'])

app = FastAPI(
    title=settings.app_name,
    description='AI-powered campus recruitment platform with job matching, RAG knowledge base, and AI interviews.',
    version='0.2.0',
    docs_url='/docs',
    redoc_url='/redoc',
    contact={'name': 'AI Campus Recruit', 'email': 'admin@campus-recruit.edu'},
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')

origins = [item.strip() for item in settings.cors_origins.split(',') if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ---- XSS Sanitization Middleware ----

class XSSSanitizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ('POST', 'PUT', 'PATCH') and request.headers.get('content-type', '').startswith('application/json'):
            try:
                body = await request.body()
                if body:
                    import bleach
                    data = json.loads(body)
                    sanitized = self._sanitize(data, bleach)
                    # Re-create request with sanitized body
                    new_body = json.dumps(sanitized, ensure_ascii=False).encode('utf-8')

                    async def receive():
                        return {'type': 'http.request', 'body': new_body}
                    request._receive = receive
            except Exception:
                pass
        return await call_next(request)

    def _sanitize(self, obj, bleach):
        if isinstance(obj, str):
            return bleach.clean(obj)
        if isinstance(obj, dict):
            return {k: self._sanitize(v, bleach) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(item, bleach) for item in obj]
        return obj


app.add_middleware(XSSSanitizeMiddleware)


# ---- Global Exception Handlers ----

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={'detail': '请求过于频繁，请稍后再试', 'code': 429})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={'detail': str(exc), 'code': 422})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception('Unhandled exception: %s', exc)
    return JSONResponse(status_code=500, content={'detail': '服务器内部错误', 'code': 500})


# ---- WebSocket Connection Manager ----

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)

    async def send_personal(self, user_id: int, message: str) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for websocket in self.active_connections.values():
            await websocket.send_text(message)


manager = ConnectionManager()


@app.on_event('startup')
def on_startup() -> None:
    init_db()
    get_redis()
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}


@app.websocket('/ws/chat/{user_id}')
async def chat_socket(websocket: WebSocket, user_id: int) -> None:
    await manager.connect(user_id, websocket)
    await manager.broadcast(f'__online:{user_id}')
    try:
        while True:
            data = await websocket.receive_text()
            # Parse structured message: "to:RECEIVER_ID:CONTENT"
            if data.startswith('to:'):
                parts = data.split(':', 2)
                if len(parts) == 3:
                    receiver_id_str, content = parts[1], parts[2]
                    try:
                        receiver_id = int(receiver_id_str)
                    except ValueError:
                        continue
                    from app.models import Message as MessageModel
                    db = SessionLocal()
                    try:
                        msg = MessageModel(
                            sender_id=user_id,
                            receiver_id=receiver_id,
                            content=content,
                            message_type='text',
                        )
                        db.add(msg)
                        db.commit()
                    except Exception:
                        db.rollback()
                    finally:
                        db.close()
                    await manager.send_personal(receiver_id, f'from:{user_id}:{content}')
            else:
                await manager.broadcast(f'user:{user_id}: {data}')
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f'__offline:{user_id}')


@app.get('/api/online-users')
def get_online_users() -> dict:
    return {'online_user_ids': list(manager.active_connections.keys())}


app.include_router(users.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(companies.router, prefix='/api')
app.include_router(students.router, prefix='/api')
app.include_router(jobs.router, prefix='/api')
app.include_router(applications.router, prefix='/api')
app.include_router(messages.router, prefix='/api')
app.include_router(ai.router, prefix='/api')
app.include_router(admin.router, prefix='/api')
app.include_router(files.router, prefix='/api')
app.include_router(favorites.router, prefix='/api')
app.include_router(notifications.router, prefix='/api')

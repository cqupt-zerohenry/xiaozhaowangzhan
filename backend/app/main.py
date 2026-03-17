from __future__ import annotations

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.cache import get_redis
from app.config import settings
from app.db import SessionLocal, init_db
from app.routers import ai, admin, applications, auth, companies, favorites, files, jobs, messages, students, users
from app.seed import seed_data

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=settings.app_name)

app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')

origins = [item.strip() for item in settings.cors_origins.split(',') if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


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
                    try:
                        receiver_id = int(parts[1])
                        content = parts[2]
                        # Persist to database
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
                        finally:
                            db.close()
                        # Send to receiver if online
                        await manager.send_personal(receiver_id, f'from:{user_id}:{content}')
                    except (ValueError, Exception):
                        pass
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

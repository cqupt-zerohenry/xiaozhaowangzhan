from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix='/files', tags=['files'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/upload', response_model=schemas.FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.FileUploadResponse:
    ext = os.path.splitext(file.filename or '')[1].lower()
    allowed = {'.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx', '.txt', '.md'}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f'File type {ext} not allowed')

    content = await file.read()
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail='File too large (max 10MB)')

    unique_name = f'{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, 'wb') as f:
        f.write(content)

    file_url = f'/uploads/{unique_name}'
    return schemas.FileUploadResponse(file_url=file_url, filename=file.filename or unique_name)

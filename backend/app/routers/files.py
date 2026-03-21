from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.storage import get_storage

router = APIRouter(prefix='/files', tags=['files'])


@router.post('/upload', response_model=schemas.FileUploadResponse, summary='Upload a file')
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

    storage = get_storage()
    file_url = storage.save(file.filename or 'unknown', content)
    return schemas.FileUploadResponse(file_url=file_url, filename=file.filename or '')

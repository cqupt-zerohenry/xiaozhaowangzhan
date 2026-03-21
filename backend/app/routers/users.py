from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.models import User
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix='/users', tags=['users'])


@router.post('', response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.UserOut:
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=400, detail='Email already exists')

    record = User(
        role=payload.role,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        status='active',
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.UserOut.model_validate(record)


@router.get('', response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> list[schemas.UserOut]:
    result = db.scalars(select(User).order_by(User.id.desc())).all()
    return [schemas.UserOut.model_validate(item) for item in result]


@router.get('/{user_id}', response_model=schemas.UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.UserOut:
    if current_user.role != 'admin' and current_user.id != user_id:
        raise HTTPException(status_code=403, detail='Permission denied')

    record = db.get(User, user_id)
    if not record:
        raise HTTPException(status_code=404, detail='User not found')
    return schemas.UserOut.model_validate(record)


@router.post('/login', response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.LoginResponse:
    record = db.scalar(select(User).where(User.email == payload.email))
    if not record or not verify_password(payload.password, record.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    if record.status != 'active':
        raise HTTPException(status_code=403, detail='User is disabled')

    token = create_access_token(str(record.id), record.role)
    return schemas.LoginResponse(user=schemas.UserOut.model_validate(record), token=token)

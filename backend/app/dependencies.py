from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/users/login')


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get('sub', 0))
    except Exception:
        raise credentials_error

    user = db.get(User, user_id)
    if user is None or user.status != 'active':
        raise credentials_error

    return user


def require_roles(*roles: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail='Permission denied')
        return current_user

    return checker


def require_self_or_roles(target_user_id: int, current_user: User, allowed_roles: set[str]) -> None:
    if current_user.id == target_user_id:
        return
    if current_user.role in allowed_roles:
        return
    raise HTTPException(status_code=403, detail='Permission denied')

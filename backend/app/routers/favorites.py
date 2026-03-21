from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Favorite, Job, User

router = APIRouter(prefix='/favorites', tags=['favorites'])


@router.post('', response_model=schemas.FavoriteOut)
def add_favorite(
    payload: schemas.FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.FavoriteOut:
    if not db.get(Job, payload.job_id):
        raise HTTPException(status_code=404, detail='Job not found')

    existed = db.scalar(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == payload.job_id,
        )
    )
    if existed:
        raise HTTPException(status_code=400, detail='Already favorited')

    record = Favorite(user_id=current_user.id, job_id=payload.job_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.FavoriteOut.model_validate(record)


@router.get('', response_model=list[schemas.FavoriteOut])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.FavoriteOut]:
    rows = db.scalars(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.id.desc())
    ).all()
    return [schemas.FavoriteOut.model_validate(item) for item in rows]


@router.delete('/{job_id}')
def remove_favorite(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    record = db.scalar(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == job_id,
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail='Favorite not found')
    db.delete(record)
    db.commit()
    return {'status': 'deleted'}

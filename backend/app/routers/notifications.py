from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Notification, User

router = APIRouter(prefix='/notifications', tags=['notifications'])


@router.get('', response_model=list[schemas.NotificationOut], summary='List notifications')
def list_notifications(
    notification_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.NotificationOut]:
    query = select(Notification).where(Notification.user_id == current_user.id)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    query = query.order_by(Notification.id.desc()).limit(limit)
    rows = db.scalars(query).all()
    return [schemas.NotificationOut.model_validate(row) for row in rows]


@router.get('/unread-count', summary='Get unread notification count')
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    count = db.scalar(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    ) or 0
    return {'count': count}


@router.patch('/{notification_id}/read', summary='Mark notification as read')
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    record = db.get(Notification, notification_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail='Notification not found')
    record.is_read = True
    db.commit()
    return {'status': 'ok'}


@router.patch('/read-all', summary='Mark all notifications as read')
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    db.commit()
    return {'status': 'ok'}

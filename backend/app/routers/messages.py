from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Message, User

router = APIRouter(prefix='/messages', tags=['messages'])


@router.post('', response_model=schemas.Message)
def send_message(
    payload: schemas.Message,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.Message:
    if current_user.role != 'admin' and payload.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail='Permission denied')

    receiver = db.get(User, payload.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail='Receiver not found')

    record = Message(**payload.model_dump(exclude={'id', 'create_time', 'is_read'}))
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.Message.model_validate(record)


@router.get('', response_model=list[schemas.Message])
def list_messages(
    peer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.Message]:
    query = select(Message)

    if current_user.role != 'admin':
        query = query.where(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        )

    if peer_id is not None:
        query = query.where(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == peer_id),
                (Message.sender_id == peer_id) & (Message.receiver_id == current_user.id),
            )
        )

    rows = db.scalars(query.order_by(Message.id.desc())).all()

    # Mark messages from peer as read
    if peer_id is not None:
        for row in rows:
            if row.receiver_id == current_user.id and not row.is_read:
                row.is_read = True
        db.commit()

    return [schemas.Message.model_validate(item) for item in rows]


@router.get('/unread-count', response_model=schemas.UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.UnreadCountResponse:
    count = db.scalar(
        select(func.count()).select_from(Message).where(
            and_(
                Message.receiver_id == current_user.id,
                Message.is_read == False,  # noqa: E712
            )
        )
    ) or 0
    return schemas.UnreadCountResponse(count=count)


@router.patch('/{message_id}/read')
def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    record = db.get(Message, message_id)
    if not record:
        raise HTTPException(status_code=404, detail='Message not found')
    if record.receiver_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Permission denied')
    record.is_read = True
    db.commit()
    return {'status': 'read'}

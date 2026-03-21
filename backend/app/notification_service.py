"""Notification creation and WebSocket push service."""
from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.models import Notification

logger = logging.getLogger(__name__)


async def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    notification_type: str = 'system',
    related_id: int | None = None,
    manager: object | None = None,
) -> Notification:
    """Create notification record and push via WebSocket if user is online."""
    record = Notification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type,
        related_id=related_id,
    )
    db.add(record)
    db.flush()

    # Try WebSocket push
    if manager and hasattr(manager, 'active_connections'):
        try:
            ws = manager.active_connections.get(user_id)
            if ws:
                payload = json.dumps({
                    'type': 'notification',
                    'data': {
                        'id': record.id,
                        'title': title,
                        'content': content,
                        'notification_type': notification_type,
                        'related_id': related_id,
                    },
                }, ensure_ascii=False)
                await ws.send_text(payload)
        except Exception:
            logger.debug('Failed to push notification via WebSocket')

    return record


def create_notification_sync(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    notification_type: str = 'system',
    related_id: int | None = None,
) -> Notification:
    """Synchronous version for use in non-async contexts."""
    record = Notification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type,
        related_id=related_id,
    )
    db.add(record)
    return record

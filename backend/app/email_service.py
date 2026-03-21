"""Email verification code service. Uses Redis for storage, SMTP or console for delivery."""
from __future__ import annotations

import logging
import random
import smtplib
import string
from email.mime.text import MIMEText

from app.cache import get_redis
from app.config import settings

logger = logging.getLogger(__name__)


def generate_verification_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def store_verification_code(email: str, code: str, purpose: str = 'register', ttl: int = 300) -> bool:
    client = get_redis()
    if client is None:
        logger.warning('Redis unavailable, cannot store verification code')
        return False
    key = f'email_code:{purpose}:{email}'
    try:
        client.setex(key, ttl, code)
        return True
    except Exception:
        logger.exception('Failed to store verification code')
        return False


def verify_code(email: str, code: str, purpose: str = 'register') -> bool:
    client = get_redis()
    if client is None:
        return False
    key = f'email_code:{purpose}:{email}'
    try:
        stored = client.get(key)
        if stored and stored == code:
            client.delete(key)
            return True
        return False
    except Exception:
        return False


def send_email(to: str, subject: str, body: str) -> bool:
    if settings.smtp_host:
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = settings.smtp_user
            msg['To'] = to
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            return True
        except Exception:
            logger.exception('Failed to send email via SMTP')
            return False
    else:
        logger.info('[SIMULATED EMAIL] To=%s, Subject=%s, Body=%s', to, subject, body)
        return True


def send_verification_email(email: str, purpose: str = 'register') -> str | None:
    code = generate_verification_code()
    if not store_verification_code(email, code, purpose):
        return None
    subject_map = {
        'register': 'AI校园招聘平台 - 注册验证码',
        'reset': 'AI校园招聘平台 - 密码重置验证码',
    }
    subject = subject_map.get(purpose, 'AI校园招聘平台 - 验证码')
    body = f'您的验证码是：{code}，有效期5分钟。请勿泄露给他人。'
    send_email(email, subject, body)
    return code

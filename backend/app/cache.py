from __future__ import annotations

import json
from typing import Any

import redis

from app.config import settings


_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def cache_get_json(key: str) -> Any | None:
    client = get_redis()
    if client is None:
        return None
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 120) -> None:
    client = get_redis()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        return


def cache_delete_prefix(prefix: str) -> None:
    client = get_redis()
    if client is None:
        return
    try:
        cursor = 0
        pattern = f"{prefix}*"
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        return

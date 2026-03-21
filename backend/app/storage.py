"""Abstract storage layer with local filesystem implementation."""
from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.config import settings

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


class StorageBackend(ABC):
    @abstractmethod
    def save(self, filename: str, content: bytes) -> str:
        """Save file and return the public URL path."""

    @abstractmethod
    def delete(self, filename: str) -> None:
        """Delete a file by its stored name."""

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Return the public URL for a file."""


class LocalStorage(StorageBackend):
    def __init__(self, upload_dir: str = UPLOAD_DIR) -> None:
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def _unique_name(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return f'{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}{ext}'

    def save(self, filename: str, content: bytes) -> str:
        unique = self._unique_name(filename)
        path = os.path.join(self.upload_dir, unique)
        with open(path, 'wb') as f:
            f.write(content)
        return f'/uploads/{unique}'

    def delete(self, filename: str) -> None:
        name = filename.split('/')[-1]
        path = os.path.join(self.upload_dir, name)
        if os.path.exists(path):
            os.remove(path)

    def get_url(self, filename: str) -> str:
        return f'/uploads/{filename}'


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage

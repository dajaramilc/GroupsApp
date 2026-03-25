"""
Abstract file-storage backend – local implementation.
Designed to be swapped for S3 later.
"""
import os
import uuid
from abc import ABC, abstractmethod

import aiofiles

from app.core.config import settings


class StorageBackend(ABC):
    """Interface for file storage – implement for S3, GCS, etc."""

    @abstractmethod
    async def save(self, file_data: bytes, filename: str) -> str:
        """Save file and return the storage path."""
        ...

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read and return file bytes."""
        ...

    @abstractmethod
    def get_full_path(self, storage_path: str) -> str:
        """Return full filesystem or URL path."""
        ...


class LocalStorageBackend(StorageBackend):
    """Saves files to local disk under settings.UPLOAD_DIR."""

    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async def save(self, file_data: bytes, filename: str) -> str:
        # Create a unique filename to avoid collisions
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = unique_name
        full_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)

        return storage_path

    async def read(self, storage_path: str) -> bytes:
        full_path = self.get_full_path(storage_path)
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    def get_full_path(self, storage_path: str) -> str:
        return os.path.join(settings.UPLOAD_DIR, storage_path)


# Singleton – swap this for S3Backend when migrating to AWS
storage_backend = LocalStorageBackend()

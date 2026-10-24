"""Storage adapter supporting local filesystem and S3."""

from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class StorageBackend(Protocol):
    async def save_file(self, key: str, data: bytes) -> str: ...

    async def get_file(self, key: str) -> bytes: ...

    async def exists(self, key: str) -> bool: ...


class FilesystemStorageBackend:
    def __init__(self, base_path: str = ".data/evidence"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        clean_key = key.lstrip("/\\")
        path = self.base_path / clean_key
        # Prevent directory traversal
        if not path.resolve().is_relative_to(self.base_path.resolve()):
            raise ValueError(f"Path traversal detected: {key}")
        return path

    async def save_file(self, key: str, data: bytes) -> str:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    async def get_file(self, key: str) -> bytes:
        path = self._resolve_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Stored file '{key}' not found.")
        return path.read_bytes()

    async def exists(self, key: str) -> bool:
        path = self._resolve_path(key)
        return path.exists()


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        settings = get_settings()
        _storage_instance = FilesystemStorageBackend(settings.LOCAL_STORAGE_PATH)
    return _storage_instance

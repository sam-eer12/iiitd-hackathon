"""Storage adapter supporting local filesystem and S3."""

import asyncio
from pathlib import Path, PurePosixPath
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


class S3StorageBackend:
    """Private evidence objects using the EC2 role, never static AWS credentials."""

    def __init__(self, bucket: str, region: str | None = None):
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    @staticmethod
    def _key(key: str) -> str:
        if not key or key.startswith("/") or "\\" in key or ".." in PurePosixPath(key).parts:
            raise ValueError("Invalid evidence object key.")
        return key

    async def save_file(self, key: str, data: bytes) -> str:
        key = self._key(key)
        await asyncio.to_thread(self.client.put_object, Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    async def get_file(self, key: str) -> bytes:
        from botocore.exceptions import ClientError

        def read() -> bytes:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
            except ClientError as exc:
                if exc.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                    raise FileNotFoundError("Evidence object not found.") from exc
                raise
            with response["Body"] as body:
                return body.read()

        return await asyncio.to_thread(read)

    async def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=self._key(key))
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                return False
            raise


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        settings = get_settings()
        if settings.STORAGE_BACKEND == "s3":
            if not settings.S3_BUCKET:
                raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3.")
            _storage_instance = S3StorageBackend(settings.S3_BUCKET, settings.AWS_REGION)
        else:
            if settings.APP_ENV == "production":
                raise ValueError("Production evidence storage must use S3.")
            _storage_instance = FilesystemStorageBackend(settings.LOCAL_STORAGE_PATH)
    return _storage_instance

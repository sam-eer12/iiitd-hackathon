"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    DATABASE_URL: str = "postgresql+asyncpg://tenderlens:tenderlens_dev@127.0.0.1:5432/tenderlens"
    DATABASE_SCHEMA: str = "tenderlens_api"

    FIREBASE_PROJECT_ID: str = "tenderlens-app-2026"
    FIREBASE_AUTH_EMULATOR_HOST: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None

    STORAGE_BACKEND: Literal["filesystem", "s3"] = "filesystem"
    LOCAL_STORAGE_PATH: str = ".data/evidence"
    AWS_REGION: str | None = None
    S3_BUCKET: str | None = None

    TINYFISH_API_KEY: str | None = None
    TINYFISH_BASE_URL: str = "https://agent.tinyfish.ai"
    TINYFISH_MODE: Literal["fixture", "live"] = "live"

    MAX_PROVIDER_CONCURRENCY: int = 1
    TINYFISH_MAX_DURATION_SECONDS: int = 300
    PROVIDER_OBSERVATION_BUDGET_SECONDS: int = 360
    PROVIDER_POLL_INTERVAL_SECONDS: int = 15
    SOURCE_CACHE_TTL_SECONDS: int = 600
    SOURCE_REFRESH_COOLDOWN_SECONDS: int = 60

    MAX_PDF_BYTES: int = 20971520  # 20 MiB
    MAX_PDF_PAGES: int = 150
    PDF_PARSE_TIMEOUT_SECONDS: int = 30
    JOB_LEASE_SECONDS: int = 90
    JOB_HEARTBEAT_SECONDS: int = 20
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

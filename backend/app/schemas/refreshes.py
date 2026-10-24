"""Schemas for refresh jobs and provider observation state."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema


class RefreshCreateRequest(BaseSchema):
    source_id: str = "iiitd"
    mode: str = "discovery"
    scope: dict[str, Any] = Field(default_factory=dict)


class RefreshProgress(BaseSchema):
    documents_discovered: int = 0
    documents_processed: int = 0


class RefreshJobDetail(BaseSchema):
    id: UUID
    source_id: str
    status: str
    stage: str
    provider_status: str | None = None
    provider_run_id: str | None = None
    cache_hit: bool = False
    progress: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None


class RefreshJobResponse(BaseSchema):
    job: RefreshJobDetail

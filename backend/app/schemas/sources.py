"""Schemas for public source configuration and freshness."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class SourceInfo(BaseSchema):
    id: str
    name: str
    startUrl: str = Field(alias="start_url")
    approvedHosts: list[str] = Field(alias="approved_hosts")
    adapterVersion: str = Field(alias="adapter_version")
    enabled: bool
    lastAcceptedAt: datetime | None = Field(default=None, alias="last_accepted_at")


class SourceListResponse(BaseSchema):
    sources: list[SourceInfo]

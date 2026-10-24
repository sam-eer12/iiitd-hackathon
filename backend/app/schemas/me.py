"""Schemas for authenticated user and workspace context."""

from datetime import datetime
from uuid import UUID

from app.schemas.common import BaseSchema


class WorkspaceInfo(BaseSchema):
    id: UUID
    name: str
    is_personal: bool = True
    role: str = "owner"
    created_at: datetime


class UserInfo(BaseSchema):
    id: UUID
    firebase_uid: str
    email: str | None = None
    display_name: str | None = None
    created_at: datetime
    last_seen_at: datetime


class MeResponse(BaseSchema):
    user: UserInfo
    workspace: WorkspaceInfo

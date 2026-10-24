"""Schemas for bookmarks / saved tenders."""

from datetime import datetime
from uuid import UUID

from app.schemas.common import BaseSchema


class BookmarkItem(BaseSchema):
    id: UUID
    workspace_id: UUID
    tender_id: UUID
    saved_at: datetime


class BookmarkListResponse(BaseSchema):
    items: list[BookmarkItem]
    total: int

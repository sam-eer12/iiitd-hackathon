"""Schemas for one-time browser local-workspace import."""

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.profiles import SupplierFacts


class LocalWorkspaceImportRequest(BaseSchema):
    import_key: str
    profile: SupplierFacts | None = None
    bookmarked_tender_ids: list[str] = Field(default_factory=list)


class LocalWorkspaceImportResponse(BaseSchema):
    imported_profile: bool
    imported_bookmarks_count: int
    rejected_bookmarks: list[str] = Field(default_factory=list)
    message: str

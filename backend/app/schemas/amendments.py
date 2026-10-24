"""Schemas for tender amendment history and clause diffs."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema

ChangeType = Literal["added", "modified", "removed", "unchanged"]


class AmendmentChangeSchema(BaseSchema):
    id: UUID
    clauseIdentity: str = Field(alias="clause_identity")
    changeType: ChangeType = Field(alias="change_type")
    beforeText: str | None = Field(default=None, alias="before_text")
    afterText: str | None = Field(default=None, alias="after_text")
    materialChange: bool = Field(default=True, alias="material_change")


class AmendmentHistoryResponse(BaseSchema):
    tenderId: UUID = Field(alias="tender_id")
    snapshotsCount: int = Field(alias="snapshots_count")
    changes: list[AmendmentChangeSchema]

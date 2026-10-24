"""Schemas for tenders, conditions, findings, and evaluations."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema

ReadinessStatus = Literal["meets", "review", "blocked"]
ConditionType = Literal["turnover", "experience", "certificate", "deposit", "deadline"]


class ConditionSchema(BaseSchema):
    id: UUID | None = None
    type: ConditionType
    label: str
    requirement: str
    quote: str
    page: int
    clause: str
    threshold: float | None = None
    years: list[str] | None = None
    certificate: str | None = None
    deadline: str | None = None
    mandatory: bool = True


class FindingSchema(BaseSchema):
    condition: ConditionSchema
    status: ReadinessStatus
    reason: str
    supplier_value: str


class EvaluationSchema(BaseSchema):
    status: ReadinessStatus
    findings: list[FindingSchema]
    coverage_complete: bool
    valid_until: datetime | None = None
    evaluated_at: datetime | None = None
    rule_version: str | None = None
    snapshot_id: UUID | None = None


class TenderSchema(BaseSchema):
    id: UUID | str
    reference: str
    title: str
    description: str = ""
    issuer: str
    category: str
    value: str
    deadline_text: str | None = None
    deadline: str | None = None
    relevance: int | None = None
    source_url: str
    pdf_urls: list[str] = Field(default_factory=list)
    amendment_urls: list[str] = Field(default_factory=list)
    provenance: Literal["sample", "live"] = "live"
    retrieved_at: datetime
    amended: bool = False
    conditions: list[ConditionSchema] = Field(default_factory=list)
    evaluation: EvaluationSchema | None = None
    saved: bool = False


class TenderListResponse(BaseSchema):
    items: list[TenderSchema]
    total: int
    next_cursor: str | None = None

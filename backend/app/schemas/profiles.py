"""Schemas for supplier profile and versioned facts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema


class TurnoverEntry(BaseSchema):
    year: str
    amount: Decimal | float | None = None


class CertificatesFacts(BaseSchema):
    gst: bool | None = None
    iso: bool | None = None
    manufacturer: bool | None = None


class SupplierFacts(BaseSchema):
    company: str = ""
    contact: str = ""
    email: str = ""
    categories: list[str] = Field(default_factory=list)
    turnover: list[TurnoverEntry] = Field(default_factory=list)
    completed_orders: int | None = None
    deposit_capacity: Decimal | float | None = None
    certificates: CertificatesFacts = Field(default_factory=CertificatesFacts)


class ProfileResponse(BaseSchema):
    id: UUID
    workspace_id: UUID
    version_number: int
    facts: SupplierFacts
    facts_provenance: str
    updated_at: datetime


class ProfileUpdateRequest(BaseSchema):
    facts: SupplierFacts
    expected_version: int | None = None
    provenance: str = "self-reported"

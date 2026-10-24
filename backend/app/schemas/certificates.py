"""Requests contain declarations and consent; verified status is response-only."""

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import BaseSchema


class VerificationStartRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["gst", "pan"]
    subject_name: str = Field(min_length=2, max_length=200)
    document_number: str = Field(min_length=10, max_length=15)
    consent: Literal[True]
    request_key: UUID
    flow: Literal["signin", "signup"] = "signin"

    @model_validator(mode="after")
    def validate_identity(self):
        self.subject_name = self.subject_name.strip()
        self.document_number = self.document_number.strip().upper()
        pattern = (
            r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]"
            if self.kind == "gst"
            else r"[A-Z]{5}[0-9]{4}[A-Z]"
        )
        if not re.fullmatch(pattern, self.document_number) or len(self.subject_name) < 2:
            raise ValueError("Enter the exact holder name and a valid GSTIN or PAN format.")
        return self


class VerificationRestartRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    consent: Literal[True]
    flow: Literal["signin", "signup"] = "signin"


class VerificationSummary(BaseSchema):
    id: UUID
    kind: Literal["gst", "pan"]
    provider: Literal["entitylocker", "digilocker"]
    environment: Literal["test", "live"]
    subject_name: str
    masked_number: str
    status: str
    message: str
    issuer: str | None
    created_at: datetime
    verified_at: datetime | None
    valid_until: datetime | None


class VerificationListResponse(BaseSchema):
    configured: bool
    available_kinds: list[Literal["gst", "pan"]]
    environment: Literal["test", "live"]
    verifications: list[VerificationSummary]


class VerificationStartResponse(BaseSchema):
    verification: VerificationSummary
    authorization_url: str | None = None

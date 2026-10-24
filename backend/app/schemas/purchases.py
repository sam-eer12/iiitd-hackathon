"""Strict demo checkout contracts. Price and purchase status are server-owned."""

from datetime import datetime
from typing import Literal
from urllib.parse import quote
from uuid import UUID

from pydantic import AwareDatetime, ConfigDict, Field, model_validator

from app.schemas.common import BaseSchema
from app.sources.iiitd import validate_discovery_result


class PurchaseTender(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=1800)
    reference: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=500)
    issuer: Literal["IIIT-Delhi"]
    source_url: str = Field(max_length=2000)
    pdf_urls: list[str] = Field(max_length=30)
    amendment_urls: list[str] = Field(max_length=30)
    deadline: AwareDatetime | None
    deadline_text: str | None = Field(max_length=1000)
    retrieved_at: AwareDatetime

    @model_validator(mode="after")
    def validate_source_snapshot(self):
        reference = self.reference.strip()
        identity = (
            reference
            if reference != "Reference not provided"
            else f"{self.source_url}|{self.title.strip()}"
        )
        # Match the existing frontend stable identity (encodeURIComponent).
        encoded = quote(identity, safe="~()*!.'-")
        if self.id != f"iiitd-{encoded}":
            raise ValueError("The tender identity does not match the source notice.")
        validate_discovery_result(
            {
                "outcome": "success",
                "notices": [
                    {
                        "notice_id": self.reference,
                        "title": self.title,
                        "source_url": self.source_url,
                        "deadline_text": self.deadline_text,
                        "pdf_urls": self.pdf_urls,
                        "amendment_urls": self.amendment_urls,
                    }
                ],
            }
        )
        return self


class PurchaseStartRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    tender: PurchaseTender
    reviewed: Literal[True]
    demo_acknowledged: Literal[True]


class DemoPaymentRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["success", "failure"]


class PurchaseResponse(BaseSchema):
    id: UUID
    tender: PurchaseTender
    supplier: dict[str, str]
    amount_paise: int
    currency: Literal["INR"]
    status: Literal["pending", "failed", "purchased"]
    identity_status: Literal["verified", "test_passed", "unverified"]
    created_at: datetime
    updated_at: datetime
    purchased_at: datetime | None
    demo: Literal[True] = True
    receipt_number: str | None = None

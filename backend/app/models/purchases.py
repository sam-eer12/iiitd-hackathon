"""Demo checkout records. These never represent real payments or awarded contracts."""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.models import utcnow


class DemoPurchase(Base):
    __tablename__ = "demo_purchases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("tenderlens_api.users.id", ondelete="CASCADE")
    )
    tender_key: Mapped[str] = mapped_column(sa.String(1800))
    tender: Mapped[dict[str, Any]] = mapped_column(JSONB)
    supplier: Mapped[dict[str, Any]] = mapped_column(JSONB)
    amount_paise: Mapped[int] = mapped_column(sa.Integer, default=49900)
    currency: Mapped[str] = mapped_column(sa.String(3), default="INR")
    status: Mapped[str] = mapped_column(sa.String(20), default="pending")
    identity_status: Mapped[str] = mapped_column(sa.String(20), default="unverified")
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    purchased_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True))

    __table_args__ = (
        sa.UniqueConstraint("workspace_id", "tender_key", name="uq_demo_purchase_tender"),
        sa.CheckConstraint(
            "status IN ('pending', 'failed', 'purchased')", name="ck_demo_purchase_status"
        ),
        sa.CheckConstraint(
            "amount_paise = 49900 AND currency = 'INR'", name="ck_demo_purchase_amount"
        ),
        sa.CheckConstraint(
            "(status = 'purchased') = (purchased_at IS NOT NULL)", name="ck_demo_purchase_receipt"
        ),
    )

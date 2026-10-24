"""Server-owned document verification receipts, separate from supplier declarations."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.models import utcnow


class CertificateVerification(Base):
    __tablename__ = "certificate_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("tenderlens_api.users.id", ondelete="CASCADE"), index=True
    )
    request_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(sa.String(30))
    provider: Mapped[str] = mapped_column(sa.String(30))
    environment: Mapped[str] = mapped_column(sa.String(10))
    subject_name: Mapped[str] = mapped_column(sa.String(200))
    document_number: Mapped[str] = mapped_column(sa.String(30))
    status: Mapped[str] = mapped_column(sa.String(30), default="submitting")
    provider_session_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    issuer: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    document_sha256: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    message: Mapped[str] = mapped_column(sa.String(500), default="Waiting for document consent.")
    consented_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("workspace_id", "request_key", name="uq_certificate_request"),
        sa.CheckConstraint("kind IN ('gst', 'pan')", name="ck_certificate_kind"),
        sa.CheckConstraint("environment IN ('test', 'live')", name="ck_certificate_environment"),
    )

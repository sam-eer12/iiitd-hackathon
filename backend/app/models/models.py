"""SQLAlchemy models for TenderLens domain and operations in tenderlens_api schema."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(
        sa.String(128), unique=True, index=True, nullable=False
    )
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow
    )

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), default="Personal Workspace")
    is_personal: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    profile: Mapped["SupplierProfile | None"] = relationship(
        back_populates="workspace", uselist=False, cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    refresh_jobs: Mapped[list["RefreshJob"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(sa.String(50), default="owner")
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    __table_args__ = (sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow
    )

    workspace: Mapped[Workspace] = relationship(back_populates="profile")
    versions: Mapped[list["SupplierProfileVersion"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class SupplierProfileVersion(Base):
    __tablename__ = "supplier_profile_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.supplier_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    facts_provenance: Mapped[str] = mapped_column(sa.String(50), default="self-reported")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    __table_args__ = (
        sa.UniqueConstraint("profile_id", "version_number", name="uq_profile_version"),
    )

    profile: Mapped[SupplierProfile] = relationship(back_populates="versions")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(sa.String(50), primary_key=True)  # e.g., 'iiitd'
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    start_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    approved_hosts: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    adapter_version: Mapped[str] = mapped_column(sa.String(50), default="v1")
    enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    last_accepted_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    tenders: Mapped[list["Tender"]] = relationship(back_populates="source")
    refresh_jobs: Mapped[list["RefreshJob"]] = relationship(back_populates="source")


class RefreshJob(Base):
    __tablename__ = "refresh_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(
        sa.String(50),
        sa.ForeignKey("tenderlens_api.sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(
        sa.String(50), default="discovery"
    )  # discovery | watched | fixture
    status: Mapped[str] = mapped_column(
        sa.String(50), default="queued", index=True
    )  # queued, running, completed, failed, cancelled
    stage: Mapped[str] = mapped_column(
        sa.String(50), default="discovery"
    )  # discovery, validating, ingesting, extracting, evaluating, publishing
    provider_status: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    provider_run_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(sa.String(255), nullable=True, index=True)
    lease_token: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(sa.Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    progress: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=lambda: {"documentsDiscovered": 0, "documentsProcessed": 0}
    )
    cache_hit: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="refresh_jobs")
    source: Mapped[Source] = relationship(back_populates="refresh_jobs")
    provider_attempts: Mapped[list["ProviderAttempt"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ProviderAttempt(Base):
    __tablename__ = "provider_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.refresh_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(sa.Integer, default=1)
    provider_run_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True, index=True)
    correlation_marker: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    provider_status: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    job: Mapped[RefreshJob] = relationship(back_populates="provider_attempts")


class SourceObservation(Base):
    __tablename__ = "source_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.refresh_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.provider_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )
    observed_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validated_notices: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    completeness: Mapped[str] = mapped_column(sa.String(50), default="complete")


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(
        sa.String(50),
        sa.ForeignKey("tenderlens_api.sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    external_reference: Mapped[str] = mapped_column(sa.String(255), index=True, nullable=False)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, default="")
    issuer: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(100), default="General")
    estimated_value: Mapped[str] = mapped_column(sa.String(100), default="")
    deadline_text: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    relevance_score: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    provenance: Mapped[str] = mapped_column(sa.String(50), default="live")  # live | sample
    amended: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow
    )

    source: Mapped[Source] = relationship(back_populates="tenders")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["TenderSnapshot"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    __table_args__ = (
        sa.UniqueConstraint("workspace_id", "tender_id", name="uq_workspace_tender_bookmark"),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="bookmarks")
    tender: Mapped[Tender] = relationship(back_populates="bookmarks")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # Null if public official document, non-null if private manual upload
    source_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    role: Mapped[str] = mapped_column(
        sa.String(50), default="main_notice"
    )  # main_notice | corrigendum | manual_upload
    visibility: Mapped[str] = mapped_column(sa.String(50), default="public")  # public | private
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    tender: Mapped[Tender] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sha256: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    byte_size: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(sa.Integer, default=0)
    observed_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    __table_args__ = (sa.UniqueConstraint("document_id", "sha256", name="uq_document_sha256"),)

    document: Mapped[Document] = relationship(back_populates="versions")
    parse_artifacts: Mapped[list["ParseArtifact"]] = relationship(
        back_populates="document_version", cascade="all, delete-orphan"
    )


class ParseArtifact(Base):
    __tablename__ = "parse_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parser_version: Mapped[str] = mapped_column(sa.String(50), default="pymupdf-v1")
    page_data: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(50), default="extracted"
    )  # extracted | failed | review_needed
    coverage_issues: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    document_version: Mapped[DocumentVersion] = relationship(back_populates="parse_artifacts")


class TenderSnapshot(Base):
    __tablename__ = "tender_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_fingerprint: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    document_version_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    effective_conditions_fingerprint: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    tender: Mapped[Tender] = relationship(back_populates="snapshots")
    conditions: Mapped[list["Condition"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tender_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        sa.String(50), nullable=False
    )  # turnover, experience, certificate, deposit, deadline
    label: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    requirement: Mapped[str] = mapped_column(sa.Text, nullable=False)
    clause_reference: Mapped[str] = mapped_column(sa.String(100), default="")
    page_number: Mapped[int] = mapped_column(sa.Integer, default=1)
    exact_quote: Mapped[str] = mapped_column(sa.Text, nullable=False)
    threshold_amount: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 2), nullable=True)
    years: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    certificate_type: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    deadline_timestamp: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    mandatory: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    snapshot: Mapped[TenderSnapshot] = relationship(back_populates="conditions")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="condition", cascade="all, delete-orphan"
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.supplier_profile_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tender_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_version: Mapped[str] = mapped_column(sa.String(50), default="rules-v1")
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)  # meets | review | blocked
    coverage_complete: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    valid_until: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    workspace: Mapped[Workspace] = relationship(back_populates="evaluations")
    snapshot: Mapped[TenderSnapshot] = relationship(back_populates="evaluations")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan"
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.conditions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)  # meets | review | blocked
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    supplier_value: Mapped[str] = mapped_column(sa.String(255), default="Not provided")
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

    evaluation: Mapped[Evaluation] = relationship(back_populates="findings")
    condition: Mapped[Condition] = relationship(back_populates="findings")


class AmendmentChange(Base):
    __tablename__ = "amendment_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tender_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenderlens_api.tender_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    clause_identity: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    change_type: Mapped[str] = mapped_column(
        sa.String(50), nullable=False
    )  # added | modified | removed | unchanged
    before_text: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    after_text: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    material_change: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=utcnow)

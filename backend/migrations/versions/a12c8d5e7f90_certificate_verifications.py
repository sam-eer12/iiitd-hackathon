"""Persist workspace-scoped certificate verification receipts.

Revision ID: a12c8d5e7f90
Revises: 5c5449f2d810
"""

import sqlalchemy as sa
from alembic import op

revision = "a12c8d5e7f90"
down_revision = "5c5449f2d810"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certificate_verifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.UUID(),
            sa.ForeignKey("tenderlens_api.workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("tenderlens_api.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_key", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("environment", sa.String(10), nullable=False),
        sa.Column("subject_name", sa.String(200), nullable=False),
        sa.Column("document_number", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("provider_session_id", sa.String(100), nullable=True),
        sa.Column("issuer", sa.String(255), nullable=True),
        sa.Column("document_sha256", sa.String(64), nullable=True),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("consented_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("valid_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("workspace_id", "request_key", name="uq_certificate_request"),
        sa.CheckConstraint("kind IN ('gst', 'pan')", name="ck_certificate_kind"),
        sa.CheckConstraint("environment IN ('test', 'live')", name="ck_certificate_environment"),
        schema="tenderlens_api",
    )
    for column in ("workspace_id", "user_id"):
        op.create_index(
            f"ix_tenderlens_api_certificate_verifications_{column}",
            "certificate_verifications",
            [column],
            schema="tenderlens_api",
        )


def downgrade() -> None:
    op.drop_table("certificate_verifications", schema="tenderlens_api")

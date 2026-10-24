"""Persist demo purchases separately from real tenders and verification receipts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b23d9e6f8a01"
down_revision = "a12c8d5e7f90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demo_purchases",
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
        sa.Column("tender_key", sa.String(1800), nullable=False),
        sa.Column("tender", postgresql.JSONB(), nullable=False),
        sa.Column("supplier", postgresql.JSONB(), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("identity_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("purchased_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        schema="tenderlens_api",
    )
    op.create_index(
        "ix_tenderlens_api_demo_purchases_workspace_id",
        "demo_purchases",
        ["workspace_id"],
        schema="tenderlens_api",
    )


def downgrade() -> None:
    op.drop_table("demo_purchases", schema="tenderlens_api")

"""Tenders, conditions, evaluations, and amendment repositories."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.models import (
    AmendmentChange,
    Bookmark,
    Condition,
    Document,
    Evaluation,
    Finding,
    Tender,
    TenderSnapshot,
)


async def get_tenders(
    db: AsyncSession,
    workspace_id: UUID,
    category: str | None = None,
    search: str | None = None,
    saved_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Tender], int]:
    stmt = (
        sa.select(Tender)
        .options(
            selectinload(Tender.documents),
            selectinload(Tender.snapshots).selectinload(TenderSnapshot.conditions),
        )
        .order_by(Tender.created_at.desc())
    )

    if get_settings().TINYFISH_MODE == "live":
        stmt = stmt.where(Tender.provenance == "live")

    if saved_only:
        stmt = stmt.join(
            Bookmark, (Bookmark.tender_id == Tender.id) & (Bookmark.workspace_id == workspace_id)
        )

    if category and category.lower() != "all":
        stmt = stmt.where(sa.func.lower(Tender.category) == category.lower())

    if search:
        search_filter = f"%{search.lower()}%"
        stmt = stmt.where(
            sa.or_(
                sa.func.lower(Tender.title).like(search_filter),
                sa.func.lower(Tender.external_reference).like(search_filter),
                sa.func.lower(Tender.description).like(search_filter),
            )
        )

    # Count total matching
    count_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one() or 0

    paged_stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(paged_stmt)
    tenders = list(result.scalars().all())
    return tenders, total


async def get_tender_by_id(db: AsyncSession, tender_id: UUID) -> Tender | None:
    stmt = (
        sa.select(Tender)
        .where(Tender.id == tender_id)
        .options(
            selectinload(Tender.documents).selectinload(Document.versions),
            selectinload(Tender.snapshots).selectinload(TenderSnapshot.conditions),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tender_conditions(db: AsyncSession, tender_id: UUID) -> list[Condition]:
    stmt = (
        sa.select(Condition)
        .join(TenderSnapshot, Condition.snapshot_id == TenderSnapshot.id)
        .where(TenderSnapshot.tender_id == tender_id, TenderSnapshot.is_current)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tender_evaluations(
    db: AsyncSession,
    tender_id: UUID,
    workspace_id: UUID,
) -> list[Evaluation]:
    stmt = (
        sa.select(Evaluation)
        .join(TenderSnapshot, Evaluation.snapshot_id == TenderSnapshot.id)
        .where(
            TenderSnapshot.tender_id == tender_id,
            Evaluation.workspace_id == workspace_id,
        )
        .options(selectinload(Evaluation.findings).selectinload(Finding.condition))
        .order_by(Evaluation.evaluated_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tender_amendments(db: AsyncSession, tender_id: UUID) -> list[AmendmentChange]:
    stmt = (
        sa.select(AmendmentChange)
        .where(AmendmentChange.tender_id == tender_id)
        .order_by(AmendmentChange.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

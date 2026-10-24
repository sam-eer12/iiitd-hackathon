"""Bookmarks repository for saved tenders."""

from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Bookmark


async def get_workspace_bookmarks(db: AsyncSession, workspace_id: UUID) -> list[Bookmark]:
    stmt = (
        sa.select(Bookmark)
        .where(Bookmark.workspace_id == workspace_id)
        .order_by(Bookmark.saved_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_bookmarked_tender_ids(db: AsyncSession, workspace_id: UUID) -> set[UUID]:
    stmt = sa.select(Bookmark.tender_id).where(Bookmark.workspace_id == workspace_id)
    result = await db.execute(stmt)
    return set(result.scalars().all())


async def add_bookmark(db: AsyncSession, workspace_id: UUID, tender_id: UUID) -> Bookmark:
    stmt = sa.select(Bookmark).where(
        Bookmark.workspace_id == workspace_id,
        Bookmark.tender_id == tender_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    bookmark = Bookmark(
        workspace_id=workspace_id,
        tender_id=tender_id,
        saved_at=datetime.now(UTC),
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


async def remove_bookmark(db: AsyncSession, workspace_id: UUID, tender_id: UUID) -> bool:
    stmt = sa.select(Bookmark).where(
        Bookmark.workspace_id == workspace_id,
        Bookmark.tender_id == tender_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if not existing:
        return False

    await db.delete(existing)
    await db.commit()
    return True

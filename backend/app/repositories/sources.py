"""Sources repository for managing public procurement portals."""

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Source


async def get_all_sources(db: AsyncSession) -> list[Source]:
    stmt = sa.select(Source).order_by(Source.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_source_by_id(db: AsyncSession, source_id: str) -> Source | None:
    stmt = sa.select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_source(
    db: AsyncSession,
    source_id: str,
    name: str,
    start_url: str,
    approved_hosts: list[str],
    adapter_version: str = "v1",
    enabled: bool = True,
) -> Source:
    source = await get_source_by_id(db, source_id)
    now = datetime.now(UTC)
    if not source:
        source = Source(
            id=source_id,
            name=name,
            start_url=start_url,
            approved_hosts=approved_hosts,
            adapter_version=adapter_version,
            enabled=enabled,
            created_at=now,
        )
        db.add(source)
    else:
        source.name = name
        source.start_url = start_url
        source.approved_hosts = approved_hosts
        source.adapter_version = adapter_version
        source.enabled = enabled

    await db.commit()
    await db.refresh(source)
    return source

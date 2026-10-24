"""Sources configuration routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.sources import get_all_sources
from app.schemas.sources import SourceInfo, SourceListResponse

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=SourceListResponse)
async def list_sources(db: AsyncSession = Depends(get_db)) -> SourceListResponse:
    sources = await get_all_sources(db)
    items = [
        SourceInfo(
            id=s.id,
            name=s.name,
            start_url=s.start_url,
            approved_hosts=s.approved_hosts,
            adapter_version=s.adapter_version,
            enabled=s.enabled,
            last_accepted_at=s.last_accepted_at,
        )
        for s in sources
    ]
    return SourceListResponse(sources=items)

"""Bookmarks routes for saving and unsaving tenders."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.errors import NotFoundError
from app.database import get_db
from app.repositories.bookmarks import (
    add_bookmark,
    get_workspace_bookmarks,
    remove_bookmark,
)
from app.repositories.tenders import get_tender_by_id
from app.schemas.bookmarks import BookmarkItem, BookmarkListResponse

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.get("", response_model=BookmarkListResponse)
async def list_bookmarks(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> BookmarkListResponse:
    bookmarks = await get_workspace_bookmarks(db, ctx.workspace_id)
    items = [
        BookmarkItem(
            id=b.id,
            workspace_id=b.workspace_id,
            tender_id=b.tender_id,
            saved_at=b.saved_at,
        )
        for b in bookmarks
    ]
    return BookmarkListResponse(items=items, total=len(items))


@router.put("/{tender_id}", status_code=status.HTTP_200_OK)
async def save_bookmark(
    tender_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        raise NotFoundError("Tender not found.")

    await add_bookmark(db, ctx.workspace_id, tender_id)
    return {"status": "saved"}


@router.delete("/{tender_id}", status_code=status.HTTP_200_OK)
async def delete_bookmark(
    tender_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    removed = await remove_bookmark(db, ctx.workspace_id, tender_id)
    return {"status": "removed" if removed else "not_found"}

"""Local-workspace browser import endpoint."""

from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.database import get_db
from app.models.models import Tender
from app.repositories.bookmarks import add_bookmark
from app.repositories.profiles import update_profile_facts
from app.schemas.imports import LocalWorkspaceImportRequest, LocalWorkspaceImportResponse

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/local-workspace", response_model=LocalWorkspaceImportResponse)
async def import_local_workspace(
    payload: LocalWorkspaceImportRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> LocalWorkspaceImportResponse:
    imported_profile = False
    if payload.profile:
        await update_profile_facts(
            db,
            workspace_id=ctx.workspace_id,
            facts=payload.profile.model_dump(),
            user_id=ctx.user_id,
            provenance="imported-browser-storage",
        )
        imported_profile = True

    imported_bookmarks_count = 0
    rejected_bookmarks: list[str] = []

    for tender_id_str in payload.bookmarked_tender_ids:
        try:
            tender_uuid = UUID(tender_id_str)
            stmt = sa.select(Tender).where(Tender.id == tender_uuid)
            res = await db.execute(stmt)
            tender = res.scalar_one_or_none()
            if tender:
                await add_bookmark(db, ctx.workspace_id, tender_uuid)
                imported_bookmarks_count += 1
            else:
                rejected_bookmarks.append(tender_id_str)
        except (ValueError, TypeError):
            # Non-UUID (such as old sample IDs or live-run IDs)
            rejected_bookmarks.append(tender_id_str)

    return LocalWorkspaceImportResponse(
        imported_profile=imported_profile,
        imported_bookmarks_count=imported_bookmarks_count,
        rejected_bookmarks=rejected_bookmarks,
        message="Local workspace data successfully imported into persistent backend.",
    )

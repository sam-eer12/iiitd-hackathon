"""Evidence retrieval and PDF streaming routes."""

from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.errors import ForbiddenError, NotFoundError
from app.database import get_db
from app.integrations.storage import get_storage
from app.models.models import DocumentVersion

router = APIRouter(prefix="/document-versions", tags=["Evidence"])


@router.get("/{id}/evidence")
async def get_document_evidence(
    id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = (
        sa.select(DocumentVersion)
        .where(DocumentVersion.id == id)
        .options(selectinload(DocumentVersion.document))
    )
    res = await db.execute(stmt)
    doc_version = res.scalar_one_or_none()
    if not doc_version:
        raise NotFoundError("Document version not found.")

    doc = doc_version.document
    # If private manual upload, verify workspace ownership
    if doc.visibility == "private" and doc.workspace_id != ctx.workspace_id:
        raise ForbiddenError("You do not have access to this document version.")

    storage = get_storage()
    try:
        data = await storage.get_file(doc_version.storage_key)
    except FileNotFoundError:
        raise NotFoundError("Stored document file is missing.")

    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={doc_version.sha256[:12]}.pdf",
            "X-Sha256": doc_version.sha256,
            "X-Page-Count": str(doc_version.page_count),
        },
    )

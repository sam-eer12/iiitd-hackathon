"""Discovery and refresh job routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.errors import NotFoundError
from app.database import get_db
from app.repositories.refreshes import (
    cancel_job,
    create_refresh_job,
    get_refresh_job,
)
from app.schemas.refreshes import (
    RefreshCreateRequest,
    RefreshJobDetail,
    RefreshJobResponse,
)

router = APIRouter(prefix="/refreshes", tags=["Refreshes"])


@router.post("", response_model=RefreshJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_refresh(
    payload: RefreshCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> RefreshJobResponse:
    job = await create_refresh_job(
        db,
        workspace_id=ctx.workspace_id,
        source_id=payload.source_id,
        mode=payload.mode,
        idempotency_key=idempotency_key,
    )
    detail = RefreshJobDetail(
        id=job.id,
        source_id=job.source_id,
        status=job.status,
        stage=job.stage,
        provider_status=job.provider_status,
        provider_run_id=job.provider_run_id,
        cache_hit=job.cache_hit,
        progress=job.progress,
        created_at=job.created_at,
        finished_at=job.finished_at,
        error_code=job.error_code,
        error_message=job.error_message,
    )
    return RefreshJobResponse(job=detail)


@router.get("/{job_id}", response_model=RefreshJobResponse)
async def get_refresh_status(
    job_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> RefreshJobResponse:
    job = await get_refresh_job(db, job_id=job_id, workspace_id=ctx.workspace_id)
    if not job:
        raise NotFoundError("Refresh job not found.")

    detail = RefreshJobDetail(
        id=job.id,
        source_id=job.source_id,
        status=job.status,
        stage=job.stage,
        provider_status=job.provider_status,
        provider_run_id=job.provider_run_id,
        cache_hit=job.cache_hit,
        progress=job.progress,
        created_at=job.created_at,
        finished_at=job.finished_at,
        error_code=job.error_code,
        error_message=job.error_message,
    )
    return RefreshJobResponse(job=detail)


@router.post("/{job_id}/cancel", response_model=RefreshJobResponse)
async def cancel_refresh(
    job_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> RefreshJobResponse:
    job = await cancel_job(db, job_id=job_id, workspace_id=ctx.workspace_id)
    if not job:
        raise NotFoundError("Refresh job not found.")

    detail = RefreshJobDetail(
        id=job.id,
        source_id=job.source_id,
        status=job.status,
        stage=job.stage,
        provider_status=job.provider_status,
        provider_run_id=job.provider_run_id,
        cache_hit=job.cache_hit,
        progress=job.progress,
        created_at=job.created_at,
        finished_at=job.finished_at,
        error_code=job.error_code,
        error_message=job.error_message,
    )
    return RefreshJobResponse(job=detail)

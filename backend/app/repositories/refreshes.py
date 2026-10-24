"""Refresh jobs repository with lease management and FOR UPDATE SKIP LOCKED claiming."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import IdempotencyConflictError
from app.models.models import RefreshJob


async def get_refresh_job(
    db: AsyncSession,
    job_id: UUID,
    workspace_id: UUID | None = None,
) -> RefreshJob | None:
    stmt = sa.select(RefreshJob).where(RefreshJob.id == job_id)
    if workspace_id:
        stmt = stmt.where(RefreshJob.workspace_id == workspace_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_refresh_job(
    db: AsyncSession,
    workspace_id: UUID,
    source_id: str,
    mode: str = "discovery",
    idempotency_key: str | None = None,
) -> RefreshJob:
    now = datetime.now(UTC)

    # Check for active job with same idempotency key
    if idempotency_key:
        stmt = sa.select(RefreshJob).where(
            RefreshJob.workspace_id == workspace_id,
            RefreshJob.idempotency_key == idempotency_key,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            if existing.source_id != source_id or existing.mode != mode:
                raise IdempotencyConflictError("Idempotency key reused with differing parameters.")
            return existing

    # Check for another currently active job for the same workspace/source
    stmt_active = sa.select(RefreshJob).where(
        RefreshJob.workspace_id == workspace_id,
        RefreshJob.source_id == source_id,
        RefreshJob.status.in_(["queued", "running"]),
    )
    res_active = await db.execute(stmt_active)
    active = res_active.scalar_one_or_none()
    if active:
        return active

    job = RefreshJob(
        workspace_id=workspace_id,
        source_id=source_id,
        mode=mode,
        status="queued",
        stage="discovery",
        idempotency_key=idempotency_key,
        progress={"documentsDiscovered": 0, "documentsProcessed": 0},
        created_at=now,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def claim_due_job(db: AsyncSession, lease_seconds: int = 90) -> tuple[RefreshJob, str] | None:
    """Claim the next queued or expired lease job using SELECT FOR UPDATE SKIP LOCKED."""
    now = datetime.now(UTC)
    lease_token = uuid4().hex

    # Find jobs that are queued, or running with an expired lease
    stmt = (
        sa.select(RefreshJob)
        .where(
            sa.or_(
                RefreshJob.status == "queued",
                sa.and_(
                    RefreshJob.status == "running",
                    RefreshJob.lease_expires_at < now,
                ),
            )
        )
        .order_by(RefreshJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        return None

    job.status = "running"
    job.lease_token = lease_token
    job.lease_expires_at = now + timedelta(seconds=lease_seconds)
    job.heartbeat_at = now
    await db.commit()
    await db.refresh(job)
    return job, lease_token


async def heartbeat_job(
    db: AsyncSession, job_id: UUID, lease_token: str, lease_seconds: int = 90
) -> bool:
    now = datetime.now(UTC)
    stmt = sa.select(RefreshJob).where(
        RefreshJob.id == job_id,
        RefreshJob.lease_token == lease_token,
        RefreshJob.status == "running",
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        return False

    job.heartbeat_at = now
    job.lease_expires_at = now + timedelta(seconds=lease_seconds)
    await db.commit()
    return True


async def complete_job(
    db: AsyncSession,
    job_id: UUID,
    lease_token: str,
    provider_status: str = "COMPLETED",
    provider_run_id: str | None = None,
    progress: dict | None = None,
) -> bool:
    now = datetime.now(UTC)
    stmt = sa.select(RefreshJob).where(
        RefreshJob.id == job_id,
        RefreshJob.lease_token == lease_token,
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        return False

    job.status = "completed"
    job.stage = "published"
    job.provider_status = provider_status
    if provider_run_id:
        job.provider_run_id = provider_run_id
    if progress:
        job.progress = progress
    job.finished_at = now
    job.lease_token = None
    job.lease_expires_at = None
    await db.commit()
    return True


async def fail_job(
    db: AsyncSession,
    job_id: UUID,
    error_code: str,
    error_message: str,
) -> None:
    now = datetime.now(UTC)
    stmt = sa.select(RefreshJob).where(RefreshJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if job:
        job.status = "failed"
        job.error_code = error_code
        job.error_message = error_message
        job.finished_at = now
        job.lease_token = None
        job.lease_expires_at = None
        await db.commit()


async def cancel_job(db: AsyncSession, job_id: UUID, workspace_id: UUID) -> RefreshJob | None:
    stmt = sa.select(RefreshJob).where(
        RefreshJob.id == job_id,
        RefreshJob.workspace_id == workspace_id,
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        return None

    if job.status in ("completed", "failed", "cancelled"):
        return job

    job.status = "cancelled"
    job.finished_at = datetime.now(UTC)
    job.lease_token = None
    job.lease_expires_at = None
    await db.commit()
    await db.refresh(job)
    return job

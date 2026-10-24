"""Public source snapshots from durable observations, excluding workspace documents."""

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.models.models import RefreshJob, SourceObservation

router = APIRouter(prefix="/catalog", tags=["Public catalog"])


@router.get("/configuration")
async def configuration() -> dict[str, bool]:
    settings = get_settings()
    return {"configured": bool(settings.TINYFISH_API_KEY), "tokenRequired": False}


@router.get("")
async def latest_catalog(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        sa.select(SourceObservation, RefreshJob.provider_run_id)
        .join(RefreshJob, SourceObservation.job_id == RefreshJob.id)
        .where(
            RefreshJob.source_id == "iiitd",
            RefreshJob.mode == "discovery",
            RefreshJob.status == "completed",
        )
        .order_by(SourceObservation.observed_at.desc())
        .limit(1)
    )
    row = result.first()
    if not row:
        return {"payload": None, "observedAt": None, "providerRunId": None}
    observation, run_id = row
    return {
        "payload": {
            "outcome": "success" if observation.validated_notices else "no_matches",
            "failure_reason": None,
            "notices": observation.validated_notices,
        },
        "observedAt": observation.observed_at.isoformat(),
        "providerRunId": run_id,
    }

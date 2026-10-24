"""Health and readiness check endpoints."""

import sqlalchemy as sa
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.integrations.storage import get_storage

router = APIRouter(tags=["Health"])


@router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> dict[str, str]:
    """Process liveness probe."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Readiness probe: checks database and storage availability."""
    checks: dict[str, str] = {}
    is_ready = True

    # 1. Database check
    try:
        stmt = sa.text("SELECT 1 FROM tenderlens_api.sources LIMIT 1")
        await db.execute(stmt)
        checks["database"] = "healthy"
    except Exception as exc:
        checks["database"] = f"unhealthy: {exc}"
        is_ready = False

    # 2. Storage check
    try:
        get_storage()
        checks["storage"] = "healthy"
    except Exception as exc:
        checks["storage"] = f"unhealthy: {exc}"
        is_ready = False

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if is_ready else "not_ready", "checks": checks},
    )

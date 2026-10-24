"""Supplier profile management routes."""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.errors import NotFoundError
from app.database import get_db
from app.repositories.profiles import get_profile_by_workspace, update_profile_facts
from app.schemas.profiles import ProfileResponse, ProfileUpdateRequest, SupplierFacts

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    pair = await get_profile_by_workspace(db, ctx.workspace_id)
    if not pair:
        raise NotFoundError("Supplier profile not found.")
    profile, version = pair
    return ProfileResponse(
        id=profile.id,
        workspace_id=profile.workspace_id,
        version_number=version.version_number,
        facts=SupplierFacts.model_validate(version.facts),
        facts_provenance=version.facts_provenance,
        updated_at=profile.updated_at,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    if_match: str | None = Header(default=None, alias="If-Match"),
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    expected_version = payload.expected_version
    if if_match and expected_version is None:
        try:
            expected_version = int(if_match.strip('"'))
        except ValueError:
            pass

    profile, version = await update_profile_facts(
        db,
        workspace_id=ctx.workspace_id,
        facts=payload.facts.model_dump(),
        expected_version=expected_version,
        user_id=ctx.user_id,
        provenance=payload.provenance,
    )

    return ProfileResponse(
        id=profile.id,
        workspace_id=profile.workspace_id,
        version_number=version.version_number,
        facts=SupplierFacts.model_validate(version.facts),
        facts_provenance=version.facts_provenance,
        updated_at=profile.updated_at,
    )

"""Supplier profile repository with immutable versioning and optimistic concurrency."""

from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProfileVersionConflictError
from app.models.models import SupplierProfile, SupplierProfileVersion


async def get_profile_by_workspace(
    db: AsyncSession,
    workspace_id: UUID,
) -> tuple[SupplierProfile, SupplierProfileVersion] | None:
    stmt = sa.select(SupplierProfile).where(SupplierProfile.workspace_id == workspace_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        return None

    if profile.current_version_id:
        v_stmt = sa.select(SupplierProfileVersion).where(
            SupplierProfileVersion.id == profile.current_version_id
        )
        v_res = await db.execute(v_stmt)
        version = v_res.scalar_one_or_none()
        if version:
            return profile, version

    # Fallback to latest version
    v_stmt = (
        sa.select(SupplierProfileVersion)
        .where(SupplierProfileVersion.profile_id == profile.id)
        .order_by(SupplierProfileVersion.version_number.desc())
    )
    v_res = await db.execute(v_stmt)
    version = v_res.scalar_one_or_none()
    if not version:
        return None
    return profile, version


async def update_profile_facts(
    db: AsyncSession,
    workspace_id: UUID,
    facts: dict,
    expected_version: int | None = None,
    user_id: UUID | None = None,
    provenance: str = "self-reported",
) -> tuple[SupplierProfile, SupplierProfileVersion]:
    pair = await get_profile_by_workspace(db, workspace_id)
    now = datetime.now(UTC)

    if not pair:
        # Create profile and version 1
        profile = SupplierProfile(
            workspace_id=workspace_id,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        await db.flush()

        version = SupplierProfileVersion(
            profile_id=profile.id,
            version_number=1,
            facts=facts,
            facts_provenance=provenance,
            created_by_user_id=user_id,
            created_at=now,
        )
        db.add(version)
        await db.flush()

        profile.current_version_id = version.id
        await db.commit()
        await db.refresh(profile)
        await db.refresh(version)
        return profile, version

    profile, current_version = pair

    # Optimistic locking check
    if expected_version is not None and expected_version != current_version.version_number:
        raise ProfileVersionConflictError(
            f"Expected profile version {expected_version}, but current version is {current_version.version_number}."
        )

    new_version_number = current_version.version_number + 1
    new_version = SupplierProfileVersion(
        profile_id=profile.id,
        version_number=new_version_number,
        facts=facts,
        facts_provenance=provenance,
        created_by_user_id=user_id,
        created_at=now,
    )
    db.add(new_version)
    await db.flush()

    profile.current_version_id = new_version.id
    profile.updated_at = now
    await db.commit()
    await db.refresh(profile)
    await db.refresh(new_version)
    return profile, new_version

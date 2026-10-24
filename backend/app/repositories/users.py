"""User and workspace repository for provisioning and membership."""

from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    SupplierProfile,
    SupplierProfileVersion,
    User,
    Workspace,
    WorkspaceMembership,
)


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User | None:
    stmt = sa.select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_workspace(db: AsyncSession, user_id: UUID) -> Workspace | None:
    stmt = (
        sa.select(Workspace)
        .join(WorkspaceMembership, Workspace.id == WorkspaceMembership.workspace_id)
        .where(WorkspaceMembership.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def provision_user_and_workspace(
    db: AsyncSession,
    firebase_uid: str,
    email: str | None = None,
    display_name: str | None = None,
) -> tuple[User, Workspace]:
    """Idempotently provision a user and personal workspace."""
    user = await get_user_by_firebase_uid(db, firebase_uid)
    now = datetime.now(UTC)

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            created_at=now,
            last_seen_at=now,
        )
        db.add(user)
        await db.flush()

        workspace = Workspace(
            name=f"{display_name or email or 'Personal'}'s Workspace",
            is_personal=True,
            created_at=now,
        )
        db.add(workspace)
        await db.flush()

        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
            created_at=now,
        )
        db.add(membership)

        # Initialize default empty supplier profile
        profile = SupplierProfile(
            workspace_id=workspace.id,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        await db.flush()

        initial_version = SupplierProfileVersion(
            profile_id=profile.id,
            version_number=1,
            facts={
                "company": "",
                "contact": "",
                "email": email or "",
                "categories": [],
                "turnover": [],
                "completedOrders": None,
                "depositCapacity": None,
                "certificates": {"gst": None, "iso": None, "manufacturer": None},
            },
            facts_provenance="initial-empty",
            created_by_user_id=user.id,
            created_at=now,
        )
        db.add(initial_version)
        await db.flush()

        profile.current_version_id = initial_version.id
        await db.commit()
        await db.refresh(user)
        await db.refresh(workspace)
        return user, workspace

    # User exists: update last seen & email/name if changed
    user.last_seen_at = now
    if email:
        user.email = email
    if display_name:
        user.display_name = display_name

    workspace = await get_user_workspace(db, user.id)
    if not workspace:
        workspace = Workspace(
            name=f"{display_name or email or 'Personal'}'s Workspace",
            is_personal=True,
            created_at=now,
        )
        db.add(workspace)
        await db.flush()
        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
            created_at=now,
        )
        db.add(membership)
        await db.flush()

    await db.commit()
    await db.refresh(user)
    await db.refresh(workspace)
    return user, workspace

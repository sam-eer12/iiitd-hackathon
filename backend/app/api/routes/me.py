"""User context and personal workspace routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context, get_current_principal
from app.core.auth import Principal
from app.core.authorization import AuthenticatedContext
from app.database import get_db
from app.repositories.users import (
    get_user_by_firebase_uid,
    get_user_workspace,
    provision_user_and_workspace,
)
from app.schemas.me import MeResponse, UserInfo, WorkspaceInfo

router = APIRouter(prefix="/me", tags=["Identity"])


@router.put("", response_model=MeResponse)
async def provision_me(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Idempotently provision or update the authenticated user and their personal workspace."""
    user, workspace = await provision_user_and_workspace(
        db,
        firebase_uid=principal.uid,
        email=principal.email,
        display_name=principal.display_name,
    )
    return MeResponse(
        user=UserInfo.model_validate(user),
        workspace=WorkspaceInfo.model_validate(workspace),
    )


@router.get("", response_model=MeResponse)
async def get_me(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Read the current authenticated user and workspace context."""
    user = await get_user_by_firebase_uid(db, ctx.principal.uid)
    workspace = await get_user_workspace(db, ctx.user_id)
    return MeResponse(
        user=UserInfo.model_validate(user),
        workspace=WorkspaceInfo.model_validate(workspace),
    )

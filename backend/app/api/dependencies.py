"""API dependency injection for database sessions and authenticated user context."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Principal, verify_id_token
from app.core.authorization import AuthenticatedContext
from app.core.errors import AuthenticationError
from app.database import get_db
from app.repositories.users import provision_user_and_workspace


async def get_current_principal(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Principal:
    if not authorization:
        raise AuthenticationError("Authorization header is missing.")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'.")

    token = parts[1]
    return verify_id_token(token)


async def get_authenticated_context(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedContext:
    user, workspace = await provision_user_and_workspace(
        db,
        firebase_uid=principal.uid,
        email=principal.email,
        display_name=principal.display_name,
    )
    return AuthenticatedContext(
        principal=principal,
        user_id=user.id,
        workspace_id=workspace.id,
    )

"""Workspace authorization and context definitions."""

from dataclasses import dataclass
from uuid import UUID

from app.core.auth import Principal
from app.core.errors import ForbiddenError


@dataclass
class AuthenticatedContext:
    principal: Principal
    user_id: UUID
    workspace_id: UUID


def ensure_workspace_access(context: AuthenticatedContext, target_workspace_id: UUID) -> None:
    if context.workspace_id != target_workspace_id:
        raise ForbiddenError("Access to this workspace is prohibited.")

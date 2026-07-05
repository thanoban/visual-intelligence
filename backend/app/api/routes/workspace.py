from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ...db import get_db
from ...dependencies import get_current_user
from ...models.entities import IntegrationProvider, User, UserRole, Workspace
from ...schemas.workspace import (
    IntegrationStatusResponse,
    UpdateWorkspaceSettingsRequest,
    WorkspaceSettingsResponse,
)
from ...serializers import serialize_workspace

router = APIRouter(prefix="/workspace", tags=["workspace"])

DEFAULT_WORKSPACE_SETTINGS = {
    "default_language_hint": "auto",
    "slack_channel": "",
    "slack_auto_post": False,
}


def _get_workspace(db: Session, workspace_id: str) -> Workspace:
    workspace = db.scalar(
        select(Workspace)
        .where(Workspace.id == workspace_id)
        .options(selectinload(Workspace.integrations))
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


def _normalized_workspace_settings(settings: dict[str, object]) -> dict[str, object]:
    default_language_hint = settings.get("default_language_hint")
    if default_language_hint not in {"auto", "en", "si", "ta"}:
        default_language_hint = DEFAULT_WORKSPACE_SETTINGS["default_language_hint"]

    slack_channel = settings.get("slack_channel")
    if not isinstance(slack_channel, str):
        slack_channel = DEFAULT_WORKSPACE_SETTINGS["slack_channel"]

    slack_auto_post = settings.get("slack_auto_post")
    if not isinstance(slack_auto_post, bool):
        slack_auto_post = DEFAULT_WORKSPACE_SETTINGS["slack_auto_post"]

    return {
        **settings,
        "default_language_hint": default_language_hint,
        "slack_channel": slack_channel,
        "slack_auto_post": slack_auto_post,
    }


def _serialize_workspace_settings(workspace: Workspace) -> WorkspaceSettingsResponse:
    connected_providers = {integration.provider.value for integration in workspace.integrations}
    return WorkspaceSettingsResponse(
        workspace=serialize_workspace(workspace).model_copy(
            update={"settings": _normalized_workspace_settings(workspace.settings)}
        ),
        integrations=[
            IntegrationStatusResponse(
                provider=provider.value,
                connected=provider.value in connected_providers,
            )
            for provider in (
                IntegrationProvider.GOOGLE,
                IntegrationProvider.SLACK,
                IntegrationProvider.JIRA,
            )
        ],
    )


@router.get("/settings", response_model=WorkspaceSettingsResponse)
def get_workspace_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceSettingsResponse:
    workspace = _get_workspace(db, current_user.workspace_id)
    return _serialize_workspace_settings(workspace)


@router.patch("/settings", response_model=WorkspaceSettingsResponse)
def update_workspace_settings(
    payload: UpdateWorkspaceSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceSettingsResponse:
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workspace owners can update settings")

    workspace = _get_workspace(db, current_user.workspace_id)
    workspace.settings = {
        **workspace.settings,
        "default_language_hint": payload.default_language_hint,
        "slack_channel": payload.slack_channel.strip(),
        "slack_auto_post": payload.slack_auto_post,
    }
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    db.refresh(workspace, attribute_names=["integrations"])
    return _serialize_workspace_settings(workspace)

from __future__ import annotations

from pydantic import BaseModel, Field

from .auth import InviteResponse, UserSummary, WorkspaceSummary


class IntegrationStatusResponse(BaseModel):
    provider: str
    connected: bool


class WorkspaceSettingsResponse(BaseModel):
    workspace: WorkspaceSummary
    integrations: list[IntegrationStatusResponse]


class WorkspaceMembersResponse(BaseModel):
    members: list[UserSummary]
    invites: list[InviteResponse]


class UpdateWorkspaceSettingsRequest(BaseModel):
    default_language_hint: str = Field(pattern="^(auto|en|si|ta)$")
    slack_channel: str = Field(default="", max_length=255)
    slack_auto_post: bool = False

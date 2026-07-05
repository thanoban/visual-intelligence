from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceSummary(BaseModel):
    id: str
    name: str
    settings: dict[str, object]
    created_at: datetime
    updated_at: datetime


class UserSummary(BaseModel):
    id: str
    email: str
    name: str
    role: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
    workspace: WorkspaceSummary


class SignUpRequest(BaseModel):
    email: str
    name: str
    password: str = Field(min_length=8)
    workspace_name: str = Field(min_length=2, max_length=255)


class SignInRequest(BaseModel):
    email: str
    password: str


class CreateInviteRequest(BaseModel):
    email: str


class AcceptInviteRequest(BaseModel):
    token: str
    email: str
    name: str
    password: str = Field(min_length=8)


class InviteResponse(BaseModel):
    id: str
    email: str
    status: str
    token: str
    workspace_id: str
    invited_by_user_id: str | None
    expires_at: datetime | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime

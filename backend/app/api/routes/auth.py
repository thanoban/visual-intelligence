from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...dependencies import get_current_user
from ...models.entities import User, UserRole, Workspace, WorkspaceInvite, WorkspaceInviteStatus
from ...schemas.auth import (
    AcceptInviteRequest,
    AuthSessionResponse,
    CreateInviteRequest,
    InviteResponse,
    SignInRequest,
    SignUpRequest,
)
from ...security import create_access_token, hash_password, verify_password
from ...serializers import serialize_invite, serialize_user, serialize_workspace

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _build_auth_session(user: User) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=create_access_token(user.id, user.workspace_id),
        user=serialize_user(user),
        workspace=serialize_workspace(user.workspace),
    )


@router.post("/sign-up", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    email = _normalize_email(payload.email)
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    workspace = Workspace(name=payload.workspace_name.strip(), settings={})
    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.OWNER,
        workspace=workspace,
    )
    db.add_all([workspace, user])
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    return _build_auth_session(user)


@router.post("/sign-in", response_model=AuthSessionResponse)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    db.refresh(user, attribute_names=["workspace"])
    return _build_auth_session(user)


@router.get("/session", response_model=AuthSessionResponse)
def get_session(current_user: User = Depends(get_current_user)) -> AuthSessionResponse:
    return _build_auth_session(current_user)


@router.post("/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    payload: CreateInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InviteResponse:
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workspace owners can invite members")

    email = _normalize_email(payload.email)
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    invite = WorkspaceInvite(
        workspace_id=current_user.workspace_id,
        email=email,
        invited_by_user_id=current_user.id,
        token=secrets.token_urlsafe(32),
        status=WorkspaceInviteStatus.PENDING,
        expires_at=_utc_now() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return serialize_invite(invite)


@router.post("/invites/accept", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def accept_invite(payload: AcceptInviteRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    email = _normalize_email(payload.email)
    invite = db.scalar(select(WorkspaceInvite).where(WorkspaceInvite.token == payload.token))
    if invite is None or invite.status != WorkspaceInviteStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    if invite.expires_at and _coerce_utc(invite.expires_at) < _utc_now():
        invite.status = WorkspaceInviteStatus.EXPIRED
        db.add(invite)
        db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite expired")

    if invite.email != email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite email does not match")

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.MEMBER,
        workspace_id=invite.workspace_id,
    )
    invite.status = WorkspaceInviteStatus.ACCEPTED
    invite.accepted_at = _utc_now()
    db.add_all([user, invite])
    db.commit()
    db.refresh(user)
    db.refresh(user, attribute_names=["workspace"])
    return _build_auth_session(user)

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class WorkspaceInviteStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class MeetingSource(StrEnum):
    UPLOAD = "upload"
    BOT = "bot"


class MeetingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionItemState(StrEnum):
    OPEN = "open"
    DISMISSED = "dismissed"
    EXPORTED = "exported"


class DraftKind(StrEnum):
    JIRA_ISSUE = "jira_issue"
    SLACK_MESSAGE = "slack_message"


class DraftStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    DISMISSED = "dismissed"


class IntegrationProvider(StrEnum):
    JIRA = "jira"
    SLACK = "slack"
    GOOGLE = "google"


class JobStage(StrEnum):
    INGEST = "ingest"
    TRANSCRIBE = "transcribe"
    DIARIZE = "diarize"
    ANALYZE = "analyze"
    DRAFT = "draft"
    NOTIFY = "notify"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class IdMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))


class Workspace(IdMixin, TimestampMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    invites: Mapped[list[WorkspaceInvite]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    meetings: Mapped[list[Meeting]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    integrations: Mapped[list[IntegrationConnection]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.MEMBER)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="users")
    owned_action_items: Mapped[list[ActionItem]] = relationship(back_populates="owner_user", foreign_keys="ActionItem.owner_user_id")
    acted_drafts: Mapped[list[Draft]] = relationship(back_populates="acted_by_user", foreign_keys="Draft.acted_by_user_id")
    sent_invites: Mapped[list[WorkspaceInvite]] = relationship(
        back_populates="invited_by_user",
        foreign_keys="WorkspaceInvite.invited_by_user_id",
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(back_populates="actor_user", foreign_keys="AuditEvent.actor_user_id")


class WorkspaceInvite(IdMixin, TimestampMixin, Base):
    __tablename__ = "workspace_invites"

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    invited_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[WorkspaceInviteStatus] = mapped_column(
        Enum(WorkspaceInviteStatus, native_enum=False),
        nullable=False,
        default=WorkspaceInviteStatus.PENDING,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workspace: Mapped[Workspace] = relationship(back_populates="invites")
    invited_by_user: Mapped[User | None] = relationship(back_populates="sent_invites", foreign_keys=[invited_by_user_id])


class Meeting(IdMixin, TimestampMixin, Base):
    __tablename__ = "meetings"

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[MeetingSource] = mapped_column(Enum(MeetingSource, native_enum=False), nullable=False)
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, native_enum=False),
        nullable=False,
        default=MeetingStatus.UPLOADED,
    )
    language_hint: Mapped[str | None] = mapped_column(String(16))
    detected_language: Mapped[str | None] = mapped_column(String(16))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    audio_object_key: Mapped[str | None] = mapped_column(String(512))
    error_reason: Mapped[str | None] = mapped_column(Text)

    workspace: Mapped[Workspace] = relationship(back_populates="meetings")
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.segment_index",
    )
    analysis: Mapped[MeetingAnalysis | None] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        uselist=False,
    )
    action_items: Mapped[list[ActionItem]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    drafts: Mapped[list[Draft]] = relationship(back_populates="meeting", cascade="all, delete-orphan")
    job_runs: Mapped[list[JobRun]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class TranscriptSegment(IdMixin, TimestampMixin, Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (UniqueConstraint("meeting_id", "segment_index", name="uq_transcript_segment_index"),)

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    speaker_label: Mapped[str | None] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language_tag: Mapped[str | None] = mapped_column(String(16))

    meeting: Mapped[Meeting] = relationship(back_populates="transcript_segments")


class MeetingAnalysis(IdMixin, TimestampMixin, Base):
    __tablename__ = "meeting_analyses"

    meeting_id: Mapped[str] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    summary_original_language: Mapped[str] = mapped_column(Text, nullable=False)
    summary_english: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)
    decisions: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="analysis")


class ActionItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "action_items"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(255))
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    due_date: Mapped[date | None] = mapped_column(Date)
    evidence_segment_ids: Mapped[list[object]] = mapped_column(JSON, default=list, nullable=False)
    state: Mapped[ActionItemState] = mapped_column(
        Enum(ActionItemState, native_enum=False),
        nullable=False,
        default=ActionItemState.OPEN,
    )

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")
    owner_user: Mapped[User | None] = relationship(back_populates="owned_action_items", foreign_keys=[owner_user_id])
    drafts: Mapped[list[Draft]] = relationship(back_populates="action_item")


class Draft(IdMixin, TimestampMixin, Base):
    __tablename__ = "drafts"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    action_item_id: Mapped[str | None] = mapped_column(ForeignKey("action_items.id", ondelete="SET NULL"))
    kind: Mapped[DraftKind] = mapped_column(Enum(DraftKind, native_enum=False), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus, native_enum=False),
        nullable=False,
        default=DraftStatus.DRAFT,
    )
    external_reference: Mapped[str | None] = mapped_column(String(255))
    acted_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    meeting: Mapped[Meeting] = relationship(back_populates="drafts")
    action_item: Mapped[ActionItem | None] = relationship(back_populates="drafts")
    acted_by_user: Mapped[User | None] = relationship(back_populates="acted_drafts", foreign_keys=[acted_by_user_id])


class IntegrationConnection(IdMixin, TimestampMixin, Base):
    __tablename__ = "integration_connections"
    __table_args__ = (UniqueConstraint("workspace_id", "provider", name="uq_workspace_provider"),)

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider, native_enum=False),
        nullable=False,
    )
    oauth_tokens_encrypted: Mapped[str | None] = mapped_column(Text)
    provider_identifiers: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="integrations")


class JobRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "job_runs"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    stage: Mapped[JobStage] = mapped_column(Enum(JobStage, native_enum=False), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False),
        nullable=False,
        default=JobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    meeting: Mapped[Meeting] = relationship(back_populates="job_runs")


class AuditEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "audit_events"

    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="audit_events")
    actor_user: Mapped[User | None] = relationship(back_populates="audit_events", foreign_keys=[actor_user_id])

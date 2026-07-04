from __future__ import annotations

from .models.entities import ActionItem, Draft, Meeting, MeetingAnalysis, TranscriptSegment, User, Workspace, WorkspaceInvite
from .schemas.auth import InviteResponse, UserSummary, WorkspaceSummary
from .schemas.meetings import (
    ActionItemResponse,
    DraftResponse,
    MeetingAnalysisResponse,
    MeetingDetailResponse,
    MeetingSummary,
    TranscriptSegmentResponse,
)


def serialize_workspace(workspace: Workspace) -> WorkspaceSummary:
    return WorkspaceSummary(
        id=workspace.id,
        name=workspace.name,
        settings=workspace.settings,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def serialize_user(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        workspace_id=user.workspace_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def serialize_invite(invite: WorkspaceInvite) -> InviteResponse:
    return InviteResponse(
        id=invite.id,
        email=invite.email,
        status=invite.status.value,
        token=invite.token,
        workspace_id=invite.workspace_id,
        invited_by_user_id=invite.invited_by_user_id,
        created_at=invite.created_at,
        updated_at=invite.updated_at,
    )


def serialize_meeting_summary(meeting: Meeting) -> MeetingSummary:
    return MeetingSummary(
        id=meeting.id,
        workspace_id=meeting.workspace_id,
        title=meeting.title,
        source=meeting.source.value,
        status=meeting.status.value,
        language_hint=meeting.language_hint,
        detected_language=meeting.detected_language,
        duration_seconds=meeting.duration_seconds,
        audio_object_key=meeting.audio_object_key,
        error_reason=meeting.error_reason,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def serialize_segment(segment: TranscriptSegment) -> TranscriptSegmentResponse:
    return TranscriptSegmentResponse(
        id=segment.id,
        index=segment.segment_index,
        start_seconds=segment.start_seconds,
        end_seconds=segment.end_seconds,
        speaker_label=segment.speaker_label,
        text=segment.text,
        language_tag=segment.language_tag,
    )


def serialize_analysis(analysis: MeetingAnalysis) -> MeetingAnalysisResponse:
    return MeetingAnalysisResponse(
        id=analysis.id,
        summary_original_language=analysis.summary_original_language,
        summary_english=analysis.summary_english,
        key_points=analysis.key_points,
        decisions=analysis.decisions,
    )


def serialize_action_item(action_item: ActionItem) -> ActionItemResponse:
    return ActionItemResponse(
        id=action_item.id,
        text=action_item.text,
        owner_name=action_item.owner_name,
        owner_user_id=action_item.owner_user_id,
        due_date=action_item.due_date,
        evidence_segment_ids=action_item.evidence_segment_ids,
        state=action_item.state.value,
    )


def serialize_draft(draft: Draft) -> DraftResponse:
    return DraftResponse(
        id=draft.id,
        action_item_id=draft.action_item_id,
        kind=draft.kind.value,
        payload=draft.payload,
        status=draft.status.value,
        external_reference=draft.external_reference,
        acted_by_user_id=draft.acted_by_user_id,
        acted_at=draft.acted_at,
    )


def serialize_meeting_detail(meeting: Meeting) -> MeetingDetailResponse:
    return MeetingDetailResponse(
        **serialize_meeting_summary(meeting).model_dump(),
        transcript_segments=[serialize_segment(segment) for segment in meeting.transcript_segments],
        analysis=serialize_analysis(meeting.analysis) if meeting.analysis else None,
        action_items=[serialize_action_item(action_item) for action_item in meeting.action_items],
        drafts=[serialize_draft(draft) for draft in meeting.drafts],
    )

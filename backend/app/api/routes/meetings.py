from __future__ import annotations

import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ...db import get_db
from ...dependencies import get_current_user
from ...models.entities import (
    ActionItemState,
    AuditEvent,
    Draft,
    DraftKind,
    DraftStatus,
    Meeting,
    MeetingAnalysis,
    MeetingSource,
    MeetingStatus,
    TranscriptSegment,
    User,
)
from ...schemas.meetings import (
    AskMeetingQuestionRequest,
    DraftResponse,
    MeetingAnswerCitationResponse,
    MeetingDetailResponse,
    MeetingListResponse,
    MeetingQuestionResponse,
    MeetingSummary,
    ReprocessResponse,
    UpdateDraftRequest,
)
from ...serializers import serialize_draft, serialize_meeting_detail, serialize_meeting_summary
from ...services.llm import MeetingLlmProvider, get_meeting_llm_provider
from ...services.orchestrator import ProcessingOrchestrator, get_processing_orchestrator
from ...services.storage import LocalStorageService, get_storage_service

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _meeting_query_for_workspace(workspace_id: str):
    return (
        select(Meeting)
        .where(Meeting.workspace_id == workspace_id)
        .options(
            selectinload(Meeting.transcript_segments),
            selectinload(Meeting.analysis),
            selectinload(Meeting.action_items),
            selectinload(Meeting.drafts),
        )
    )


def _meeting_search_filter(query: str):
    search_term = f"%{query}%"
    transcript_matches = select(TranscriptSegment.meeting_id).where(TranscriptSegment.text.ilike(search_term))
    return or_(
        Meeting.title.ilike(search_term),
        Meeting.detected_language.ilike(search_term),
        Meeting.language_hint.ilike(search_term),
        Meeting.id.in_(transcript_matches),
    )


def _get_workspace_meeting(db: Session, workspace_id: str, meeting_id: str) -> Meeting:
    meeting = db.scalar(_meeting_query_for_workspace(workspace_id).where(Meeting.id == meeting_id))
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_workspace_meeting_draft(db: Session, workspace_id: str, meeting_id: str, draft_id: str) -> tuple[Meeting, Draft]:
    meeting = _get_workspace_meeting(db, workspace_id, meeting_id)
    draft = next((candidate for candidate in meeting.drafts if candidate.id == draft_id), None)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return meeting, draft


def _assert_draft_editable(draft: Draft) -> None:
    if draft.status != DraftStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only drafts in draft status can be edited or reviewed",
        )


def _build_updated_draft_payload(draft: Draft, payload_patch: dict[str, object]) -> dict[str, object]:
    next_payload = {**draft.payload, **payload_patch}

    if draft.kind == DraftKind.JIRA_ISSUE:
        if not isinstance(next_payload.get("summary"), str) or not str(next_payload["summary"]).strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Jira drafts require a summary")
        if not isinstance(next_payload.get("description"), str) or not str(next_payload["description"]).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Jira drafts require a description",
            )
        evidence_segment_ids = next_payload.get("evidence_segment_ids")
        if not isinstance(evidence_segment_ids, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Jira drafts require evidence_segment_ids",
            )
        return next_payload

    if draft.kind == DraftKind.SLACK_MESSAGE:
        if not isinstance(next_payload.get("title"), str) or not str(next_payload["title"]).strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Slack drafts require a title")
        if not isinstance(next_payload.get("summary_english"), str) or not str(next_payload["summary_english"]).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Slack drafts require an English summary",
            )
        action_items = next_payload.get("action_items")
        if not isinstance(action_items, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Slack drafts require an action_items list",
            )
        return next_payload

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported draft kind")


def _record_draft_audit_event(*, db: Session, current_user: User, meeting_id: str, draft: Draft, action: str) -> None:
    db.add(
        AuditEvent(
            workspace_id=current_user.workspace_id,
            actor_user_id=current_user.id,
            action=action,
            target_type="draft",
            target_id=draft.id,
            metadata_json={
                "meeting_id": meeting_id,
                "draft_kind": draft.kind.value,
                "draft_status": draft.status.value,
            },
        )
    )


@router.post("/upload", response_model=MeetingSummary, status_code=status.HTTP_201_CREATED)
def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    language_hint: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: LocalStorageService = Depends(get_storage_service),
    orchestrator: ProcessingOrchestrator = Depends(get_processing_orchestrator),
) -> MeetingSummary:
    normalized_title = (title or Path(file.filename or "meeting").stem).strip()
    if not normalized_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting title is required")

    meeting = Meeting(
        workspace_id=current_user.workspace_id,
        title=normalized_title,
        source=MeetingSource.UPLOAD,
        status=MeetingStatus.UPLOADED,
        language_hint=language_hint.strip() if language_hint else None,
    )
    db.add(meeting)
    db.flush()

    audio_object_key = storage.save_meeting_upload(current_user.workspace_id, meeting.id, file)
    meeting.audio_object_key = audio_object_key

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    orchestrator.enqueue_meeting(meeting.id, background_tasks=background_tasks)
    return serialize_meeting_summary(meeting)


@router.get("", response_model=MeetingListResponse)
def list_meetings(
    limit: int = 20,
    offset: int = 0,
    query: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingListResponse:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    normalized_query = query.strip() if query else ""

    count_query = select(func.count(Meeting.id)).where(Meeting.workspace_id == current_user.workspace_id)
    meetings_query = _meeting_query_for_workspace(current_user.workspace_id)
    if normalized_query:
        search_filter = _meeting_search_filter(normalized_query)
        count_query = count_query.where(search_filter)
        meetings_query = meetings_query.where(search_filter)

    total = db.scalar(count_query) or 0
    meetings = list(
        db.scalars(
            meetings_query
            .order_by(Meeting.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    return MeetingListResponse(items=[serialize_meeting_summary(meeting) for meeting in meetings], total=total)


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting_detail(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetailResponse:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)
    return serialize_meeting_detail(meeting)


@router.get("/{meeting_id}/drafts", response_model=list[DraftResponse])
def list_meeting_drafts(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DraftResponse]:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)
    return [serialize_draft(draft) for draft in meeting.drafts]


@router.patch("/{meeting_id}/drafts/{draft_id}", response_model=DraftResponse)
def update_meeting_draft(
    meeting_id: str,
    draft_id: str,
    payload: UpdateDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    meeting, draft = _get_workspace_meeting_draft(db, current_user.workspace_id, meeting_id, draft_id)
    _assert_draft_editable(draft)

    draft.payload = _build_updated_draft_payload(draft, payload.payload)
    db.add(draft)
    _record_draft_audit_event(
        db=db,
        current_user=current_user,
        meeting_id=meeting.id,
        draft=draft,
        action="draft.updated",
    )
    db.commit()
    db.refresh(draft)
    return serialize_draft(draft)


@router.post("/{meeting_id}/drafts/{draft_id}/approve", response_model=DraftResponse)
def approve_meeting_draft(
    meeting_id: str,
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    meeting, draft = _get_workspace_meeting_draft(db, current_user.workspace_id, meeting_id, draft_id)
    _assert_draft_editable(draft)

    draft.status = DraftStatus.APPROVED
    draft.acted_by_user_id = current_user.id
    draft.acted_at = _utc_now()
    db.add(draft)
    _record_draft_audit_event(
        db=db,
        current_user=current_user,
        meeting_id=meeting.id,
        draft=draft,
        action="draft.approved",
    )
    db.commit()
    db.refresh(draft)
    return serialize_draft(draft)


@router.post("/{meeting_id}/drafts/{draft_id}/dismiss", response_model=DraftResponse)
def dismiss_meeting_draft(
    meeting_id: str,
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    meeting, draft = _get_workspace_meeting_draft(db, current_user.workspace_id, meeting_id, draft_id)
    _assert_draft_editable(draft)

    draft.status = DraftStatus.DISMISSED
    draft.acted_by_user_id = current_user.id
    draft.acted_at = _utc_now()
    db.add(draft)
    if draft.action_item is not None:
        draft.action_item.state = ActionItemState.DISMISSED
        db.add(draft.action_item)
    _record_draft_audit_event(
        db=db,
        current_user=current_user,
        meeting_id=meeting.id,
        draft=draft,
        action="draft.dismissed",
    )
    db.commit()
    db.refresh(draft)
    return serialize_draft(draft)


@router.get("/{meeting_id}/audio")
def get_meeting_audio(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: LocalStorageService = Depends(get_storage_service),
) -> FileResponse:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)
    if not meeting.audio_object_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting audio not found")

    audio_path = storage.resolve_relative_path(meeting.audio_object_key)
    if not audio_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting audio not found")

    media_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
    return FileResponse(audio_path, media_type=media_type, filename=audio_path.name)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: LocalStorageService = Depends(get_storage_service),
) -> Response:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)

    storage.delete_meeting_artifacts(current_user.workspace_id, meeting.id)
    db.delete(meeting)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{meeting_id}/reprocess", response_model=ReprocessResponse, status_code=status.HTTP_202_ACCEPTED)
def reprocess_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: ProcessingOrchestrator = Depends(get_processing_orchestrator),
) -> ReprocessResponse:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)
    meeting.status = MeetingStatus.UPLOADED
    meeting.error_reason = None
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    orchestrator.enqueue_meeting(meeting.id, background_tasks=background_tasks)
    return ReprocessResponse(id=meeting.id, status=meeting.status.value)


@router.post("/{meeting_id}/chat", response_model=MeetingQuestionResponse)
def ask_meeting_question(
    meeting_id: str,
    payload: AskMeetingQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_provider: MeetingLlmProvider = Depends(get_meeting_llm_provider),
) -> MeetingQuestionResponse:
    meeting = _get_workspace_meeting(db, current_user.workspace_id, meeting_id)
    if not meeting.transcript_segments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meeting transcript is not ready for question answering",
        )

    answer = llm_provider.answer_question(
        meeting_title=meeting.title,
        segments=meeting.transcript_segments,
        question=payload.question,
    )
    segments_by_id = {segment.id: segment for segment in meeting.transcript_segments}
    citations = [
        MeetingAnswerCitationResponse(
            segment_id=segment.id,
            start_seconds=segment.start_seconds,
            end_seconds=segment.end_seconds,
            speaker_label=segment.speaker_label,
            text=segment.text,
        )
        for segment_id in answer.cited_segment_ids
        if (segment := segments_by_id.get(segment_id)) is not None
    ]
    return MeetingQuestionResponse(
        answer_text=answer.answer_text,
        not_discussed=answer.not_discussed,
        citations=citations,
    )

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ...db import get_db
from ...dependencies import get_current_user
from ...models.entities import Draft, Meeting, MeetingAnalysis, MeetingSource, MeetingStatus, TranscriptSegment, User
from ...schemas.meetings import MeetingDetailResponse, MeetingListResponse, MeetingSummary, ReprocessResponse
from ...serializers import serialize_meeting_detail, serialize_meeting_summary
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


def _get_workspace_meeting(db: Session, workspace_id: str, meeting_id: str) -> Meeting:
    meeting = db.scalar(_meeting_query_for_workspace(workspace_id).where(Meeting.id == meeting_id))
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingListResponse:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    total = db.scalar(select(func.count(Meeting.id)).where(Meeting.workspace_id == current_user.workspace_id)) or 0
    meetings = list(
        db.scalars(
            _meeting_query_for_workspace(current_user.workspace_id)
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

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class MeetingSummary(BaseModel):
    id: str
    workspace_id: str
    title: str
    source: str
    status: str
    language_hint: str | None
    detected_language: str | None
    duration_seconds: float | None
    audio_object_key: str | None
    error_reason: str | None
    created_at: datetime
    updated_at: datetime


class TranscriptSegmentResponse(BaseModel):
    id: str
    index: int
    start_seconds: float
    end_seconds: float
    speaker_label: str | None
    text: str
    language_tag: str | None


class MeetingAnalysisResponse(BaseModel):
    id: str
    summary_original_language: str
    summary_english: str
    key_points: list[object]
    decisions: list[object]


class ActionItemResponse(BaseModel):
    id: str
    text: str
    owner_name: str | None
    owner_user_id: str | None
    due_date: date | None
    evidence_segment_ids: list[object]
    state: str


class DraftResponse(BaseModel):
    id: str
    action_item_id: str | None
    kind: str
    payload: dict[str, object]
    status: str
    external_reference: str | None
    acted_by_user_id: str | None
    acted_at: datetime | None


class UpdateDraftRequest(BaseModel):
    payload: dict[str, object] = Field(default_factory=dict)


class MeetingDetailResponse(MeetingSummary):
    transcript_segments: list[TranscriptSegmentResponse]
    analysis: MeetingAnalysisResponse | None
    action_items: list[ActionItemResponse]
    drafts: list[DraftResponse]


class MeetingListResponse(BaseModel):
    items: list[MeetingSummary]
    total: int


class ReprocessResponse(BaseModel):
    id: str
    status: str


class AskMeetingQuestionRequest(BaseModel):
    question: str


class MeetingAnswerCitationResponse(BaseModel):
    segment_id: str
    start_seconds: float
    end_seconds: float
    speaker_label: str | None
    text: str


class MeetingQuestionResponse(BaseModel):
    answer_text: str
    not_discussed: bool
    citations: list[MeetingAnswerCitationResponse]

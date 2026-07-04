from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker, selectinload

from ..models.entities import (
    ActionItem,
    Draft,
    DraftKind,
    DraftStatus,
    JobRun,
    JobStage,
    JobStatus,
    Meeting,
    MeetingAnalysis,
    MeetingStatus,
    TranscriptSegment,
)
from .mock_providers import MockLlmProvider, MockTranscriptionProvider

PIPELINE_STAGES = [JobStage.INGEST, JobStage.TRANSCRIBE, JobStage.ANALYZE, JobStage.DRAFT]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StageFailureInjector:
    def maybe_fail(self, meeting_id: str, stage: JobStage, attempt: int) -> None:
        raise NotImplementedError


class NoStageFailureInjector(StageFailureInjector):
    def maybe_fail(self, meeting_id: str, stage: JobStage, attempt: int) -> None:
        return None


@dataclass
class FailOnceStageFailureInjector(StageFailureInjector):
    planned_failures: dict[tuple[str, JobStage], int] = field(default_factory=dict)

    def schedule_failure(self, meeting_id: str, stage: JobStage, times: int = 1) -> None:
        self.planned_failures[(meeting_id, stage)] = self.planned_failures.get((meeting_id, stage), 0) + times

    def maybe_fail(self, meeting_id: str, stage: JobStage, attempt: int) -> None:
        _ = attempt
        key = (meeting_id, stage)
        remaining = self.planned_failures.get(key, 0)
        if remaining <= 0:
            return

        if remaining == 1:
            self.planned_failures.pop(key, None)
        else:
            self.planned_failures[key] = remaining - 1

        raise RuntimeError(f"Forced failure at {stage.value} stage")


@dataclass
class PipelineProcessor:
    session_factory: sessionmaker
    transcription_provider: MockTranscriptionProvider
    llm_provider: MockLlmProvider
    failure_injector: StageFailureInjector
    max_attempts_per_stage: int = 2

    def process_meeting(self, meeting_id: str) -> None:
        with self.session_factory() as db:
            meeting = self._load_meeting(db, meeting_id)
            start_stage = self._resolve_start_stage(db, meeting)
            self._clear_outputs_from_stage(db, meeting, start_stage)
            meeting.status = MeetingStatus.PROCESSING
            meeting.error_reason = None
            db.add(meeting)
            db.commit()

            for stage in PIPELINE_STAGES[PIPELINE_STAGES.index(start_stage) :]:
                stage_success = self._run_stage_with_retries(db, meeting_id, stage)
                if not stage_success:
                    return

            meeting = self._load_meeting(db, meeting_id)
            meeting.status = MeetingStatus.COMPLETED
            meeting.error_reason = None
            db.add(meeting)
            db.commit()

    def _run_stage_with_retries(self, db: Session, meeting_id: str, stage: JobStage) -> bool:
        last_error: str | None = None

        for attempt in range(1, self.max_attempts_per_stage + 1):
            job_run = JobRun(
                meeting_id=meeting_id,
                stage=stage,
                attempt=attempt,
                status=JobStatus.RUNNING,
                started_at=_utc_now(),
            )
            db.add(job_run)
            db.commit()

            try:
                self.failure_injector.maybe_fail(meeting_id, stage, attempt)
                meeting = self._load_meeting(db, meeting_id)
                self._run_stage(db, meeting, stage)
                job_run = db.get(JobRun, job_run.id)
                job_run.status = JobStatus.SUCCEEDED
                job_run.finished_at = _utc_now()
                db.add(job_run)
                db.commit()
                return True
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                db.rollback()
                persisted_job_run = db.get(JobRun, job_run.id)
                if persisted_job_run is not None:
                    persisted_job_run.status = JobStatus.FAILED
                    persisted_job_run.finished_at = _utc_now()
                    persisted_job_run.error = last_error
                    db.add(persisted_job_run)
                    db.commit()

                if attempt < self.max_attempts_per_stage:
                    time.sleep(min(0.05 * attempt, 0.1))

        meeting = self._load_meeting(db, meeting_id)
        meeting.status = MeetingStatus.FAILED
        meeting.error_reason = f"{stage.value} failed: {last_error}"
        db.add(meeting)
        db.commit()
        return False

    def _run_stage(self, db: Session, meeting: Meeting, stage: JobStage) -> None:
        if stage == JobStage.INGEST:
            self._run_ingest(meeting)
        elif stage == JobStage.TRANSCRIBE:
            self._run_transcribe(db, meeting)
        elif stage == JobStage.ANALYZE:
            self._run_analyze(db, meeting)
        elif stage == JobStage.DRAFT:
            self._run_draft(db, meeting)
        else:
            raise ValueError(f"Unsupported stage: {stage.value}")

        db.add(meeting)
        db.commit()

    def _run_ingest(self, meeting: Meeting) -> None:
        if not meeting.audio_object_key:
            raise FileNotFoundError("Meeting upload is missing a stored audio file")

    def _run_transcribe(self, db: Session, meeting: Meeting) -> None:
        audio_path = Path(meeting.audio_object_key)
        transcription = self.transcription_provider.transcribe(audio_path=audio_path, language_hint=meeting.language_hint)

        for segment in list(meeting.transcript_segments):
            db.delete(segment)
        meeting.transcript_segments = []
        db.flush()

        meeting.detected_language = transcription.dominant_language
        meeting.duration_seconds = transcription.duration_seconds

        for index, segment in enumerate(transcription.segments):
            db.add(
                TranscriptSegment(
                    meeting_id=meeting.id,
                    segment_index=index,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    speaker_label=segment.speaker_label,
                    text=segment.text,
                    language_tag=segment.language_tag,
                )
            )

        db.flush()

    def _run_analyze(self, db: Session, meeting: Meeting) -> None:
        segments = list(
            db.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.meeting_id == meeting.id)
                .order_by(TranscriptSegment.segment_index.asc())
            )
        )
        if not segments:
            raise RuntimeError("Cannot analyze a meeting without transcript segments")

        analysis_result = self.llm_provider.analyze_meeting(meeting.title, segments)

        if meeting.analysis is not None:
            db.delete(meeting.analysis)
            meeting.analysis = None

        for action_item in list(meeting.action_items):
            db.delete(action_item)
        meeting.action_items = []
        db.flush()

        db.add(
            MeetingAnalysis(
                meeting_id=meeting.id,
                summary_original_language=analysis_result.summary_original_language,
                summary_english=analysis_result.summary_english,
                key_points=analysis_result.key_points,
                decisions=analysis_result.decisions,
            )
        )

        for action_item in analysis_result.action_items:
            db.add(
                ActionItem(
                    meeting_id=meeting.id,
                    text=action_item.text,
                    owner_name=action_item.owner_name,
                    due_date=None,
                    evidence_segment_ids=action_item.evidence_segment_ids,
                )
            )

        db.flush()

    def _run_draft(self, db: Session, meeting: Meeting) -> None:
        for draft in list(meeting.drafts):
            db.delete(draft)
        meeting.drafts = []
        db.flush()

        action_items = list(db.scalars(select(ActionItem).where(ActionItem.meeting_id == meeting.id)))
        analysis = db.scalar(select(MeetingAnalysis).where(MeetingAnalysis.meeting_id == meeting.id))
        if analysis is None:
            raise RuntimeError("Cannot create drafts before analysis exists")

        for action_item in action_items:
            db.add(
                Draft(
                    meeting_id=meeting.id,
                    action_item_id=action_item.id,
                    kind=DraftKind.JIRA_ISSUE,
                    status=DraftStatus.DRAFT,
                    payload={
                        "summary": action_item.text,
                        "description": f"Meeting: {meeting.title}\nOwner: {action_item.owner_name or 'Unassigned'}",
                        "evidence_segment_ids": action_item.evidence_segment_ids,
                    },
                )
            )

        db.add(
            Draft(
                meeting_id=meeting.id,
                action_item_id=None,
                kind=DraftKind.SLACK_MESSAGE,
                status=DraftStatus.DRAFT,
                payload={
                    "title": meeting.title,
                    "summary_english": analysis.summary_english,
                    "action_items": [
                        {
                            "text": action_item.text,
                            "owner_name": action_item.owner_name,
                        }
                        for action_item in action_items
                    ],
                },
            )
        )
        db.flush()

    def _resolve_start_stage(self, db: Session, meeting: Meeting) -> JobStage:
        latest_failed_job = db.scalar(
            select(JobRun)
            .where(JobRun.meeting_id == meeting.id, JobRun.status == JobStatus.FAILED)
            .order_by(JobRun.created_at.desc())
            .limit(1)
        )
        if latest_failed_job is not None and meeting.status == MeetingStatus.FAILED:
            return latest_failed_job.stage
        return JobStage.INGEST

    def _clear_outputs_from_stage(self, db: Session, meeting: Meeting, start_stage: JobStage) -> None:
        if start_stage in {JobStage.INGEST, JobStage.TRANSCRIBE}:
            for segment in list(meeting.transcript_segments):
                db.delete(segment)
            meeting.transcript_segments = []
            meeting.detected_language = None
            meeting.duration_seconds = None

        if start_stage in {JobStage.INGEST, JobStage.TRANSCRIBE, JobStage.ANALYZE}:
            if meeting.analysis is not None:
                db.delete(meeting.analysis)
                meeting.analysis = None
            for action_item in list(meeting.action_items):
                db.delete(action_item)
            meeting.action_items = []

        if start_stage in {JobStage.INGEST, JobStage.TRANSCRIBE, JobStage.ANALYZE, JobStage.DRAFT}:
            for draft in list(meeting.drafts):
                db.delete(draft)
            meeting.drafts = []

        db.flush()

    def _load_meeting(self, db: Session, meeting_id: str) -> Meeting:
        meeting = db.scalar(
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.transcript_segments),
                selectinload(Meeting.analysis),
                selectinload(Meeting.action_items),
                selectinload(Meeting.drafts),
            )
        )
        if meeting is None:
            raise RuntimeError("Meeting not found for processing")
        return meeting

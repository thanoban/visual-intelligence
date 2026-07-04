from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from fastapi import BackgroundTasks

from ..db import SessionLocal
from .llm import get_meeting_llm_provider
from .mock_providers import MockTranscriptionProvider
from .pipeline import NoStageFailureInjector, PipelineProcessor


class ProcessingOrchestrator:
    def enqueue_meeting(self, meeting_id: str, background_tasks: BackgroundTasks | None = None) -> None:
        raise NotImplementedError


class NoOpProcessingOrchestrator(ProcessingOrchestrator):
    def enqueue_meeting(self, meeting_id: str, background_tasks: BackgroundTasks | None = None) -> None:
        return None


@dataclass
class RecordingProcessingOrchestrator(ProcessingOrchestrator):
    enqueued_meeting_ids: list[str] = field(default_factory=list)

    def enqueue_meeting(self, meeting_id: str, background_tasks: BackgroundTasks | None = None) -> None:
        self.enqueued_meeting_ids.append(meeting_id)


@dataclass
class BackgroundProcessingOrchestrator(ProcessingOrchestrator):
    processor: PipelineProcessor

    def enqueue_meeting(self, meeting_id: str, background_tasks: BackgroundTasks | None = None) -> None:
        if background_tasks is None:
            self.processor.process_meeting(meeting_id)
            return

        background_tasks.add_task(self.processor.process_meeting, meeting_id)


@lru_cache
def get_processing_orchestrator() -> ProcessingOrchestrator:
    processor = PipelineProcessor(
        session_factory=SessionLocal,
        transcription_provider=MockTranscriptionProvider(),
        llm_provider=get_meeting_llm_provider(),
        failure_injector=NoStageFailureInjector(),
    )
    return BackgroundProcessingOrchestrator(processor=processor)

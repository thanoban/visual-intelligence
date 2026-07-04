from __future__ import annotations

from dataclasses import dataclass, field


class ProcessingOrchestrator:
    def enqueue_meeting(self, meeting_id: str) -> None:
        raise NotImplementedError


class NoOpProcessingOrchestrator(ProcessingOrchestrator):
    def enqueue_meeting(self, meeting_id: str) -> None:
        return None


@dataclass
class RecordingProcessingOrchestrator(ProcessingOrchestrator):
    enqueued_meeting_ids: list[str] = field(default_factory=list)

    def enqueue_meeting(self, meeting_id: str) -> None:
        self.enqueued_meeting_ids.append(meeting_id)


_default_orchestrator = NoOpProcessingOrchestrator()


def get_processing_orchestrator() -> ProcessingOrchestrator:
    return _default_orchestrator

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from backend.app.config import Settings
from backend.app.models.entities import TranscriptSegment
from backend.app.services.llm import (
    AnthropicMeetingLlmProvider,
    MeetingQuestionOutputModel,
    build_anthropic_meeting_llm_provider,
    build_vertex_meeting_llm_provider,
    chunk_transcript_segments,
)


def _build_segments() -> list[TranscriptSegment]:
    return [
        TranscriptSegment(id="seg-1", meeting_id="m1", segment_index=0, start_seconds=0.0, end_seconds=10.0, speaker_label="A", text="Kickoff", language_tag="en"),
        TranscriptSegment(id="seg-2", meeting_id="m1", segment_index=1, start_seconds=10.0, end_seconds=20.0, speaker_label="B", text="Status", language_tag="en"),
        TranscriptSegment(id="seg-3", meeting_id="m1", segment_index=2, start_seconds=20.0, end_seconds=30.0, speaker_label="C", text="Blocker", language_tag="en"),
        TranscriptSegment(id="seg-4", meeting_id="m1", segment_index=3, start_seconds=30.0, end_seconds=40.0, speaker_label="D", text="Decision", language_tag="en"),
    ]


def test_chunk_transcript_segments_uses_overlap_windows() -> None:
    chunks = chunk_transcript_segments(_build_segments(), window_seconds=25, overlap_seconds=5)

    assert len(chunks) == 2
    assert [segment.id for segment in chunks[0].segments] == ["seg-1", "seg-2", "seg-3"]
    assert [segment.id for segment in chunks[1].segments] == ["seg-3", "seg-4"]


def test_chunk_transcript_segments_returns_single_chunk_for_short_transcript() -> None:
    chunks = chunk_transcript_segments(_build_segments()[:2], window_seconds=120, overlap_seconds=10)

    assert len(chunks) == 1
    assert [segment.id for segment in chunks[0].segments] == ["seg-1", "seg-2"]


class _FakeStructuredStream:
    def __init__(self, parsed_output: MeetingQuestionOutputModel) -> None:
        self._parsed_output = parsed_output

    def __enter__(self) -> "_FakeStructuredStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get_final_message(self) -> SimpleNamespace:
        return SimpleNamespace(parsed_output=self._parsed_output)

    def get_final_text(self) -> str:
        return self._parsed_output.model_dump_json()


class _RecordingMessagesApi:
    def __init__(self, parsed_output: MeetingQuestionOutputModel) -> None:
        self._parsed_output = parsed_output
        self.calls: list[dict[str, object]] = []

    def stream(self, **kwargs: object) -> _FakeStructuredStream:
        self.calls.append(dict(kwargs))
        return _FakeStructuredStream(self._parsed_output)


def test_anthropic_stream_request_omits_removed_sampling_parameters() -> None:
    messages_api = _RecordingMessagesApi(
        MeetingQuestionOutputModel(
            answer_text="Not discussed in this meeting.",
            cited_segment_ids=[],
            not_discussed=True,
        )
    )
    provider = AnthropicMeetingLlmProvider(
        client=SimpleNamespace(messages=messages_api),
        settings=Settings(
            llm_provider="claude",
            claude_model="claude-opus-4-8",
            llm_max_output_tokens=16000,
        ),
    )

    answer = provider.answer_question("Planning Sync", _build_segments()[:2], "Was billing discussed?")

    assert answer.not_discussed is True
    assert len(messages_api.calls) == 1
    request_kwargs = messages_api.calls[0]
    assert request_kwargs["model"] == "claude-opus-4-8"
    assert request_kwargs["max_tokens"] == 16000
    assert request_kwargs["thinking"] == {"type": "adaptive"}
    assert request_kwargs["output_config"] == {"effort": "high"}
    assert request_kwargs["output_format"] is MeetingQuestionOutputModel
    assert "temperature" not in request_kwargs
    assert "top_p" not in request_kwargs
    assert "top_k" not in request_kwargs


def test_anthropic_smoke_analysis_skips_without_api_key() -> None:
    pytest.importorskip("anthropic")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY is not configured")

    provider = build_anthropic_meeting_llm_provider(
        Settings(
            anthropic_api_key=api_key,
            llm_provider="claude",
            claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
        )
    )
    analysis = provider.analyze_meeting("Smoke Meeting", _build_segments())

    assert analysis.summary_english
    assert analysis.key_points or analysis.decisions or analysis.action_items


def test_vertex_smoke_analysis_skips_without_vertex_config() -> None:
    pytest.importorskip("anthropic")
    project_id = os.getenv("VERTEX_PROJECT_ID")
    if not project_id:
        pytest.skip("VERTEX_PROJECT_ID is not configured")

    provider = build_vertex_meeting_llm_provider(
        Settings(
            llm_provider="claude_vertex",
            claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
            vertex_project_id=project_id,
            vertex_region=os.getenv("VERTEX_REGION", "global"),
        )
    )
    analysis = provider.analyze_meeting("Vertex Smoke Meeting", _build_segments())

    assert analysis.summary_english

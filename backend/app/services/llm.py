from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol, TypeVar, cast

from pydantic import BaseModel, Field

from ..config import Settings, get_settings
from ..models.entities import TranscriptSegment

try:
    from anthropic import Anthropic, AnthropicVertex
except ImportError:  # pragma: no cover - optional dependency for live providers
    Anthropic = None
    AnthropicVertex = None

TStructuredModel = TypeVar("TStructuredModel", bound=BaseModel)

ANALYSIS_SYSTEM_PROMPT = """
You analyze software-team meeting transcripts.

Meetings may mix English, Sinhala, and Tamil in the same sentence. Extract only
facts that are explicitly supported by the transcript. Always produce an English
summary even if the meeting was not spoken in English. Only assign an owner when
the transcript clearly supports it. Every key point, decision, and action item
must cite supporting transcript segment ids from the provided transcript.
""".strip()

QUESTION_SYSTEM_PROMPT = """
You answer questions about a single meeting transcript.

Answer only from the provided transcript. Meetings may mix English, Sinhala,
and Tamil in the same sentence. If the transcript does not answer the question,
set `not_discussed` to true, use the exact answer text `Not discussed in this meeting.`,
and provide no cited segment ids.
""".strip()


@dataclass(frozen=True)
class ActionItemData:
    text: str
    owner_name: str | None
    due_date: str | None
    evidence_segment_ids: list[str]


@dataclass(frozen=True)
class MeetingAnalysisResult:
    summary_original_language: str
    summary_english: str
    key_points: list[dict[str, object]]
    decisions: list[dict[str, object]]
    action_items: list[ActionItemData]


@dataclass(frozen=True)
class MeetingAnswerResult:
    answer_text: str
    cited_segment_ids: list[str]
    not_discussed: bool


@dataclass(frozen=True)
class TranscriptChunk:
    index: int
    start_seconds: float
    end_seconds: float
    segments: list[TranscriptSegment]


class MeetingLlmProvider(Protocol):
    def analyze_meeting(self, meeting_title: str, segments: list[TranscriptSegment]) -> MeetingAnalysisResult:
        ...

    def answer_question(
        self,
        meeting_title: str,
        segments: list[TranscriptSegment],
        question: str,
    ) -> MeetingAnswerResult:
        ...


class EvidenceItemModel(BaseModel):
    text: str
    evidence_segment_ids: list[str] = Field(default_factory=list)


class StructuredActionItemModel(BaseModel):
    text: str
    owner_name: str | None = None
    due_date: str | None = None
    evidence_segment_ids: list[str] = Field(default_factory=list)


class MeetingAnalysisOutputModel(BaseModel):
    summary_original_language: str
    summary_english: str
    key_points: list[EvidenceItemModel] = Field(default_factory=list)
    decisions: list[EvidenceItemModel] = Field(default_factory=list)
    action_items: list[StructuredActionItemModel] = Field(default_factory=list)


class MeetingQuestionOutputModel(BaseModel):
    answer_text: str
    cited_segment_ids: list[str] = Field(default_factory=list)
    not_discussed: bool = False


class MockLlmProvider:
    def analyze_meeting(self, meeting_title: str, segments: list[TranscriptSegment]) -> MeetingAnalysisResult:
        _ = meeting_title
        first_segment_id = segments[0].id
        second_segment_id = segments[1].id
        third_segment_id = segments[2].id

        return MeetingAnalysisResult(
            summary_original_language="Team eka deploy plan eka discuss kala saha verify karana weda beda gatta.",
            summary_english="The team paused the deploy, assigned staging verification, and planned a Slack update after QA.",
            key_points=[
                {
                    "text": "The deploy should wait until staging is verified.",
                    "evidence_segment_ids": [first_segment_id, second_segment_id],
                },
                {
                    "text": "A client-facing Slack update will be sent after QA passes.",
                    "evidence_segment_ids": [third_segment_id],
                },
            ],
            decisions=[
                {
                    "text": "Do not deploy until staging verification is complete.",
                    "evidence_segment_ids": [first_segment_id, second_segment_id],
                }
            ],
            action_items=[
                ActionItemData(
                    text="Verify the login fix in staging before the deploy window.",
                    owner_name=segments[1].speaker_label,
                    due_date=None,
                    evidence_segment_ids=[second_segment_id],
                ),
                ActionItemData(
                    text="Post the client update in Slack after QA passes.",
                    owner_name=segments[2].speaker_label,
                    due_date=None,
                    evidence_segment_ids=[third_segment_id],
                ),
            ],
        )

    def answer_question(
        self,
        meeting_title: str,
        segments: list[TranscriptSegment],
        question: str,
    ) -> MeetingAnswerResult:
        _ = meeting_title
        question_text = question.lower()
        if "deploy" in question_text or "mokakda" in question_text or "decide" in question_text:
            return MeetingAnswerResult(
                answer_text="They decided to wait for the deploy until staging verification was complete.",
                cited_segment_ids=[segments[0].id, segments[1].id],
                not_discussed=False,
            )

        return MeetingAnswerResult(
            answer_text="Not discussed in this meeting.",
            cited_segment_ids=[],
            not_discussed=True,
        )


def chunk_transcript_segments(
    segments: list[TranscriptSegment],
    *,
    window_seconds: int,
    overlap_seconds: int,
) -> list[TranscriptChunk]:
    if not segments:
        return []

    effective_window = max(1, window_seconds)
    effective_overlap = max(0, min(overlap_seconds, effective_window - 1))
    final_end = max(segment.end_seconds for segment in segments)
    window_start = segments[0].start_seconds
    chunks: list[TranscriptChunk] = []
    seen_ranges: set[tuple[str, ...]] = set()

    while window_start <= final_end:
        window_end = window_start + effective_window
        chunk_segments = [
            segment
            for segment in segments
            if segment.start_seconds < window_end and segment.end_seconds > window_start
        ]
        if not chunk_segments:
            break

        segment_ids = tuple(segment.id for segment in chunk_segments)
        if segment_ids in seen_ranges:
            break

        seen_ranges.add(segment_ids)
        chunks.append(
            TranscriptChunk(
                index=len(chunks),
                start_seconds=chunk_segments[0].start_seconds,
                end_seconds=chunk_segments[-1].end_seconds,
                segments=chunk_segments,
            )
        )

        if chunk_segments[-1].id == segments[-1].id:
            break

        next_window_start = max(window_end - effective_overlap, chunk_segments[0].start_seconds + 0.001)
        if next_window_start <= window_start:
            next_window_start = window_end
        window_start = next_window_start

    return chunks


def format_segments_for_prompt(segments: list[TranscriptSegment]) -> str:
    lines: list[str] = []
    for segment in segments:
        speaker = segment.speaker_label or "Unknown speaker"
        language_label = f" [{segment.language_tag}]" if segment.language_tag else ""
        lines.append(
            f"{segment.id} | {segment.start_seconds:.2f}-{segment.end_seconds:.2f} | "
            f"{speaker}{language_label}: {segment.text}"
        )
    return "\n".join(lines)


class AnthropicMeetingLlmProvider:
    def __init__(self, *, client: Any, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    def analyze_meeting(self, meeting_title: str, segments: list[TranscriptSegment]) -> MeetingAnalysisResult:
        transcript_chunks = chunk_transcript_segments(
            segments,
            window_seconds=self._settings.llm_chunk_window_seconds,
            overlap_seconds=self._settings.llm_chunk_overlap_seconds,
        )
        if not transcript_chunks:
            raise RuntimeError("Cannot analyze a meeting without transcript segments")

        if len(transcript_chunks) == 1:
            single_output = self._parse_structured_response(
                output_model=MeetingAnalysisOutputModel,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_prompt=self._build_single_analysis_prompt(meeting_title, transcript_chunks[0].segments),
            )
            return self._convert_analysis_output(single_output)

        partial_results = [
            self._parse_structured_response(
                output_model=MeetingAnalysisOutputModel,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_prompt=self._build_chunk_analysis_prompt(meeting_title, chunk),
            )
            for chunk in transcript_chunks
        ]

        consolidated_output = self._parse_structured_response(
            output_model=MeetingAnalysisOutputModel,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=self._build_consolidation_prompt(
                meeting_title=meeting_title,
                segments=segments,
                partial_results=partial_results,
            ),
        )
        return self._convert_analysis_output(consolidated_output)

    def answer_question(
        self,
        meeting_title: str,
        segments: list[TranscriptSegment],
        question: str,
    ) -> MeetingAnswerResult:
        transcript_chunks = chunk_transcript_segments(
            segments,
            window_seconds=self._settings.llm_chunk_window_seconds,
            overlap_seconds=self._settings.llm_chunk_overlap_seconds,
        )
        if not transcript_chunks:
            raise RuntimeError("Cannot answer a question without transcript segments")

        if len(transcript_chunks) == 1:
            output = self._parse_structured_response(
                output_model=MeetingQuestionOutputModel,
                system_prompt=QUESTION_SYSTEM_PROMPT,
                user_prompt=self._build_single_question_prompt(
                    meeting_title=meeting_title,
                    segments=transcript_chunks[0].segments,
                    question=question,
                ),
            )
            return MeetingAnswerResult(
                answer_text=output.answer_text,
                cited_segment_ids=output.cited_segment_ids,
                not_discussed=output.not_discussed,
            )

        partial_answers = [
            self._parse_structured_response(
                output_model=MeetingQuestionOutputModel,
                system_prompt=QUESTION_SYSTEM_PROMPT,
                user_prompt=self._build_chunk_question_prompt(
                    meeting_title=meeting_title,
                    chunk=chunk,
                    question=question,
                ),
            )
            for chunk in transcript_chunks
        ]

        consolidated_output = self._parse_structured_response(
            output_model=MeetingQuestionOutputModel,
            system_prompt=QUESTION_SYSTEM_PROMPT,
            user_prompt=self._build_question_consolidation_prompt(
                meeting_title=meeting_title,
                segments=segments,
                question=question,
                partial_answers=partial_answers,
            ),
        )
        return MeetingAnswerResult(
            answer_text=consolidated_output.answer_text,
            cited_segment_ids=consolidated_output.cited_segment_ids,
            not_discussed=consolidated_output.not_discussed,
        )

    def _parse_structured_response(
        self,
        *,
        output_model: type[TStructuredModel],
        system_prompt: str,
        user_prompt: str,
    ) -> TStructuredModel:
        messages_api = self._client.messages
        if hasattr(messages_api, "parse"):
            parsed_response = messages_api.parse(
                model=self._settings.claude_model,
                max_tokens=self._settings.llm_max_output_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                thinking={"type": "adaptive"},
                output_config={"effort": self._settings.llm_effort},
                output_format=output_model,
                temperature=0,
            )
            parsed_output = getattr(parsed_response, "parsed_output", None)
            if parsed_output is None:
                raise RuntimeError("Anthropic structured output parsing returned no parsed output")
            return cast(TStructuredModel, parsed_output)

        raw_response = messages_api.create(
            model=self._settings.claude_model,
            max_tokens=self._settings.llm_max_output_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            thinking={"type": "adaptive"},
            output_config={
                "effort": self._settings.llm_effort,
                "format": {
                    "type": "json_schema",
                    "schema": output_model.model_json_schema(),
                },
            },
            temperature=0,
        )
        response_text = "".join(
            block.text for block in raw_response.content if getattr(block, "type", None) == "text"
        ).strip()
        if not response_text:
            raise RuntimeError("Anthropic structured output returned no text content")
        return output_model.model_validate_json(response_text)

    def _build_single_analysis_prompt(self, meeting_title: str, segments: list[TranscriptSegment]) -> str:
        return (
            f"Meeting title: {meeting_title}\n"
            "Return a complete meeting analysis for the transcript below.\n\n"
            f"{format_segments_for_prompt(segments)}"
        )

    def _build_chunk_analysis_prompt(self, meeting_title: str, chunk: TranscriptChunk) -> str:
        return (
            f"Meeting title: {meeting_title}\n"
            f"Transcript chunk: {chunk.index + 1}\n"
            "Return a partial analysis for only the transcript chunk below. Use only the segment ids shown.\n\n"
            f"{format_segments_for_prompt(chunk.segments)}"
        )

    def _build_consolidation_prompt(
        self,
        *,
        meeting_title: str,
        segments: list[TranscriptSegment],
        partial_results: list[MeetingAnalysisOutputModel],
    ) -> str:
        partial_json = json.dumps([result.model_dump() for result in partial_results], ensure_ascii=True, indent=2)
        return (
            f"Meeting title: {meeting_title}\n"
            "Merge the partial analyses below into one final meeting analysis. Deduplicate overlapping points, "
            "keep only items supported by the transcript, and preserve segment-id evidence references.\n\n"
            "Transcript reference:\n"
            f"{format_segments_for_prompt(segments)}\n\n"
            "Partial analyses JSON:\n"
            f"{partial_json}"
        )

    def _build_single_question_prompt(
        self,
        *,
        meeting_title: str,
        segments: list[TranscriptSegment],
        question: str,
    ) -> str:
        return (
            f"Meeting title: {meeting_title}\n"
            f"Question: {question}\n\n"
            "Answer the question using only the transcript below.\n\n"
            f"{format_segments_for_prompt(segments)}"
        )

    def _build_chunk_question_prompt(
        self,
        *,
        meeting_title: str,
        chunk: TranscriptChunk,
        question: str,
    ) -> str:
        return (
            f"Meeting title: {meeting_title}\n"
            f"Transcript chunk: {chunk.index + 1}\n"
            f"Question: {question}\n\n"
            "Answer the question using only the transcript chunk below.\n\n"
            f"{format_segments_for_prompt(chunk.segments)}"
        )

    def _build_question_consolidation_prompt(
        self,
        *,
        meeting_title: str,
        segments: list[TranscriptSegment],
        question: str,
        partial_answers: list[MeetingQuestionOutputModel],
    ) -> str:
        partial_json = json.dumps([answer.model_dump() for answer in partial_answers], ensure_ascii=True, indent=2)
        return (
            f"Meeting title: {meeting_title}\n"
            f"Question: {question}\n\n"
            "Decide on the best final answer using the transcript and the candidate chunk answers below. "
            "If none of the transcript supports the answer, return `Not discussed in this meeting.` with no citations.\n\n"
            "Transcript reference:\n"
            f"{format_segments_for_prompt(segments)}\n\n"
            "Candidate chunk answers JSON:\n"
            f"{partial_json}"
        )

    def _convert_analysis_output(self, output: MeetingAnalysisOutputModel) -> MeetingAnalysisResult:
        return MeetingAnalysisResult(
            summary_original_language=output.summary_original_language,
            summary_english=output.summary_english,
            key_points=[item.model_dump() for item in output.key_points],
            decisions=[item.model_dump() for item in output.decisions],
            action_items=[
                ActionItemData(
                    text=item.text,
                    owner_name=item.owner_name,
                    due_date=item.due_date,
                    evidence_segment_ids=item.evidence_segment_ids,
                )
                for item in output.action_items
            ],
        )


def build_anthropic_meeting_llm_provider(settings: Settings) -> MeetingLlmProvider:
    if Anthropic is None:
        raise RuntimeError("The anthropic package is required for llm_provider=claude")
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for llm_provider=claude")
    client = Anthropic(api_key=settings.anthropic_api_key)
    return AnthropicMeetingLlmProvider(client=client, settings=settings)


def build_vertex_meeting_llm_provider(settings: Settings) -> MeetingLlmProvider:
    if AnthropicVertex is None:
        raise RuntimeError("The anthropic package with Vertex support is required for llm_provider=claude_vertex")
    if not settings.vertex_project_id:
        raise RuntimeError("VERTEX_PROJECT_ID is required for llm_provider=claude_vertex")
    client = AnthropicVertex(project_id=settings.vertex_project_id, region=settings.vertex_region)
    return AnthropicMeetingLlmProvider(client=client, settings=settings)


@lru_cache
def get_meeting_llm_provider() -> MeetingLlmProvider:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockLlmProvider()
    if settings.llm_provider == "claude":
        return build_anthropic_meeting_llm_provider(settings)
    if settings.llm_provider == "claude_vertex":
        return build_vertex_meeting_llm_provider(settings)
    raise RuntimeError(f"Unsupported llm_provider: {settings.llm_provider}")

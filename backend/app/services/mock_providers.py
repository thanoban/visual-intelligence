from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models.entities import TranscriptSegment


@dataclass(frozen=True)
class TranscriptSegmentData:
    start_seconds: float
    end_seconds: float
    speaker_label: str
    text: str
    language_tag: str


@dataclass(frozen=True)
class TranscriptionResult:
    dominant_language: str
    duration_seconds: float
    segments: list[TranscriptSegmentData]


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


class MockTranscriptionProvider:
    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        _ = audio_path
        hint = (language_hint or "en").lower()

        if hint == "si":
            segments = [
                TranscriptSegmentData(0.0, 12.0, "Asha", "Ada deploy eka freeze karanna one.", "si"),
                TranscriptSegmentData(12.0, 25.0, "Ravi", "I will verify the login fix in staging before 4 pm.", "en"),
                TranscriptSegmentData(25.0, 39.0, "Nisha", "QA pass unoth client update eka Slack eke danna.", "si"),
            ]
            dominant_language = "si"
        elif hint == "ta":
            segments = [
                TranscriptSegmentData(0.0, 10.0, "Kavin", "Innaiku deploy plan final pannalam.", "ta"),
                TranscriptSegmentData(10.0, 23.0, "Maya", "I will validate the billing patch in staging.", "en"),
                TranscriptSegmentData(23.0, 36.0, "Kavin", "QA mudinja piragu Slack update anuppalam.", "ta"),
            ]
            dominant_language = "ta"
        else:
            segments = [
                TranscriptSegmentData(0.0, 11.0, "Asha", "We should freeze the deploy until staging looks clean.", "en"),
                TranscriptSegmentData(11.0, 24.0, "Ravi", "Hari, mama login fix eka 4 pm wenakan verify karannam.", "si"),
                TranscriptSegmentData(24.0, 36.0, "Nisha", "Once QA passes, I will post the client update in Slack.", "en"),
            ]
            dominant_language = "en"

        return TranscriptionResult(
            dominant_language=dominant_language,
            duration_seconds=segments[-1].end_seconds,
            segments=segments,
        )


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

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .llm import ActionItemData, MeetingAnalysisResult, MockLlmProvider


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

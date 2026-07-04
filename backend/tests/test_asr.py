from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

from backend.app.config import Settings
from backend.app.services.asr import RoutedSpeechTranscriptionProvider, build_transcription_provider
from backend.app.services.audio import normalize_audio_to_wav
from backend.app.services.benchmarking import (
    compute_character_error_rate,
    compute_word_error_rate,
    normalize_metric_text,
)
from backend.app.services.mock_providers import TranscriptSegmentData, TranscriptionResult


@dataclass
class FakeSpeechProvider:
    result: TranscriptionResult
    calls: list[tuple[str, str | None]]

    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        self.calls.append((str(audio_path), language_hint))
        return self.result


def test_routed_provider_prefers_explicit_language_hint() -> None:
    baseline = FakeSpeechProvider(
        result=TranscriptionResult(dominant_language="en", duration_seconds=12.0, segments=[]),
        calls=[],
    )
    sinhala = FakeSpeechProvider(
        result=TranscriptionResult(dominant_language="si", duration_seconds=12.0, segments=[]),
        calls=[],
    )
    provider = RoutedSpeechTranscriptionProvider(
        baseline_provider=baseline,
        language_providers={"si": sinhala},
    )

    result = provider.transcribe(Path("meeting.wav"), "si")

    assert result.dominant_language == "si"
    assert baseline.calls == []
    assert sinhala.calls == [("meeting.wav", "si")]


def test_routed_provider_uses_detected_language_for_reroute() -> None:
    baseline = FakeSpeechProvider(
        result=TranscriptionResult(
            dominant_language="ta",
            duration_seconds=12.0,
            segments=[
                TranscriptSegmentData(
                    start_seconds=0.0,
                    end_seconds=1.0,
                    speaker_label=None,
                    text="baseline",
                    language_tag="ta",
                )
            ],
        ),
        calls=[],
    )
    tamil = FakeSpeechProvider(
        result=TranscriptionResult(dominant_language="ta", duration_seconds=10.0, segments=[]),
        calls=[],
    )
    provider = RoutedSpeechTranscriptionProvider(
        baseline_provider=baseline,
        language_providers={"ta": tamil},
    )

    result = provider.transcribe(Path("meeting.wav"), None)

    assert result.dominant_language == "ta"
    assert baseline.calls == [("meeting.wav", None)]
    assert tamil.calls == [("meeting.wav", "ta")]


def test_build_transcription_provider_returns_mock_provider() -> None:
    provider = build_transcription_provider(Settings(asr_provider="mock"))

    result = provider.transcribe(Path("demo.wav"), "en")

    assert result.dominant_language == "en"
    assert len(result.segments) == 3


def test_word_and_character_error_rate_are_computed() -> None:
    assert normalize_metric_text("  Hello   WORLD ") == "hello world"
    assert compute_word_error_rate("hello world", "hello brave world") == 0.5
    assert compute_character_error_rate("abc", "adc") == (1 / 3)


def test_normalize_audio_to_wav_copies_wav_without_ffmpeg(tmp_path: Path) -> None:
    source_path = tmp_path / "source.wav"
    target_path = tmp_path / "normalized.wav"
    source_path.write_bytes(b"RIFFdemo")

    normalized_path = normalize_audio_to_wav(
        source_path=source_path,
        target_path=target_path,
        sample_rate_hz=16000,
        channels=1,
    )

    assert normalized_path == target_path.resolve()
    assert target_path.read_bytes() == b"RIFFdemo"


def test_benchmark_script_help_runs_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(Path("backend") / "scripts" / "benchmark_asr.py"), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Run the local ASR benchmark harness." in result.stdout

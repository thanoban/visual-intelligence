from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Protocol

from ..config import Settings, get_settings
from .mock_providers import MockTranscriptionProvider, TranscriptSegmentData, TranscriptionResult

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - optional dependency
    WhisperModel = None

try:
    import torch
except ImportError:  # pragma: no cover - optional dependency
    torch = None

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - optional dependency
    pipeline = None

SUPPORTED_LANGUAGE_HINTS = {"auto", "en", "si", "ta"}


class SpeechTranscriptionProvider(Protocol):
    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        ...


def normalize_language_hint(language_hint: str | None) -> str | None:
    if not language_hint:
        return None

    normalized = language_hint.strip().lower()
    if not normalized or normalized == "auto":
        return None
    if normalized in SUPPORTED_LANGUAGE_HINTS:
        return normalized
    return normalized


def _resolve_torch_device(configured_device: str) -> str:
    if configured_device != "auto":
        return configured_device

    if torch is not None and getattr(torch, "cuda", None) is not None and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _resolve_compute_type(settings: Settings, device: str) -> str:
    if settings.asr_compute_type != "auto":
        return settings.asr_compute_type
    return "float16" if device == "cuda" else "int8"


@dataclass
class FasterWhisperTranscriptionProvider:
    model_id: str
    settings: Settings

    @cached_property
    def _model(self):
        if WhisperModel is None:
            raise RuntimeError("The faster-whisper package is required for asr_provider=whisper or hf")

        device = _resolve_torch_device(self.settings.asr_device)
        compute_type = _resolve_compute_type(self.settings, device)
        return WhisperModel(self.model_id, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        normalized_hint = normalize_language_hint(language_hint)
        segments, info = self._model.transcribe(
            str(audio_path),
            beam_size=self.settings.asr_beam_size,
            language=normalized_hint,
            task="transcribe",
            condition_on_previous_text=False,
            vad_filter=self.settings.asr_vad_filter,
        )
        collected_segments = list(segments)
        dominant_language = getattr(info, "language", None) or normalized_hint or "unknown"
        return TranscriptionResult(
            dominant_language=dominant_language,
            duration_seconds=max((segment.end for segment in collected_segments), default=0.0),
            segments=[
                TranscriptSegmentData(
                    start_seconds=segment.start,
                    end_seconds=segment.end,
                    speaker_label=None,
                    text=segment.text.strip(),
                    language_tag=dominant_language,
                )
                for segment in collected_segments
            ],
        )


@dataclass
class HuggingFaceWhisperTranscriptionProvider:
    model_id: str
    settings: Settings
    forced_language: str

    @cached_property
    def _pipeline(self):
        if pipeline is None:
            raise RuntimeError("The transformers package is required for asr_provider=hf")

        if torch is not None and getattr(torch, "cuda", None) is not None and torch.cuda.is_available():
            device = 0
        else:
            device = -1
        return pipeline(
            task="automatic-speech-recognition",
            model=self.model_id,
            device=device,
            chunk_length_s=30,
        )

    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        normalized_hint = normalize_language_hint(language_hint) or self.forced_language
        result = self._pipeline(
            str(audio_path),
            return_timestamps=True,
            generate_kwargs={
                "language": normalized_hint,
                "task": "transcribe",
            },
        )
        chunks = result.get("chunks") or []
        return TranscriptionResult(
            dominant_language=normalized_hint,
            duration_seconds=max((chunk.get("timestamp", (0.0, 0.0))[1] or 0.0 for chunk in chunks), default=0.0),
            segments=[
                TranscriptSegmentData(
                    start_seconds=float(chunk.get("timestamp", (0.0, 0.0))[0] or 0.0),
                    end_seconds=float(chunk.get("timestamp", (0.0, 0.0))[1] or 0.0),
                    speaker_label=None,
                    text=str(chunk.get("text", "")).strip(),
                    language_tag=normalized_hint,
                )
                for chunk in chunks
            ],
        )


@dataclass
class RoutedSpeechTranscriptionProvider:
    baseline_provider: SpeechTranscriptionProvider
    language_providers: dict[str, SpeechTranscriptionProvider]

    def transcribe(self, audio_path: Path, language_hint: str | None) -> TranscriptionResult:
        normalized_hint = normalize_language_hint(language_hint)

        if normalized_hint in self.language_providers:
            return self.language_providers[normalized_hint].transcribe(audio_path, normalized_hint)

        if normalized_hint == "en":
            return self.baseline_provider.transcribe(audio_path, "en")

        baseline_result = self.baseline_provider.transcribe(audio_path, None)
        detected_language = normalize_language_hint(baseline_result.dominant_language)
        if detected_language in self.language_providers:
            return self.language_providers[detected_language].transcribe(audio_path, detected_language)

        return baseline_result


def build_transcription_provider(settings: Settings) -> SpeechTranscriptionProvider:
    if settings.asr_provider == "mock":
        return MockTranscriptionProvider()

    if settings.asr_provider == "whisper":
        return FasterWhisperTranscriptionProvider(model_id=settings.asr_model_en, settings=settings)

    if settings.asr_provider == "hf":
        return RoutedSpeechTranscriptionProvider(
            baseline_provider=FasterWhisperTranscriptionProvider(model_id=settings.asr_model_en, settings=settings),
            language_providers={
                "si": HuggingFaceWhisperTranscriptionProvider(
                    model_id=settings.asr_model_si,
                    settings=settings,
                    forced_language="si",
                ),
                "ta": HuggingFaceWhisperTranscriptionProvider(
                    model_id=settings.asr_model_ta,
                    settings=settings,
                    forced_language="ta",
                ),
            },
        )

    raise RuntimeError(f"Unsupported asr_provider: {settings.asr_provider}")


@lru_cache
def get_transcription_provider() -> SpeechTranscriptionProvider:
    return build_transcription_provider(get_settings())

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .asr import SpeechTranscriptionProvider
from .audio import normalize_audio_to_wav

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".mp4", ".webm", ".flac"}


@dataclass(frozen=True)
class BenchmarkSample:
    sample_id: str
    audio_path: Path
    reference_path: Path
    language_hint: str | None


@dataclass(frozen=True)
class BenchmarkSampleResult:
    sample_id: str
    audio_path: str
    language_hint: str | None
    dominant_language: str
    transcription: str
    wer: float
    cer: float
    duration_seconds: float
    elapsed_seconds: float


@dataclass(frozen=True)
class BenchmarkReport:
    provider: str
    sample_count: int
    mean_wer: float
    mean_cer: float
    mean_realtime_factor: float
    samples: list[BenchmarkSampleResult]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True, indent=2)


def build_benchmark_samples(samples_dir: Path, default_language_hint: str | None = None) -> list[BenchmarkSample]:
    root = samples_dir.resolve()
    samples: list[BenchmarkSample] = []

    for audio_path in sorted(path for path in root.rglob("*") if path.suffix.lower() in AUDIO_EXTENSIONS):
        reference_path = audio_path.with_suffix(".txt")
        if not reference_path.exists():
            raise FileNotFoundError(f"Missing reference transcript for {audio_path}")

        relative_path = audio_path.relative_to(root)
        inferred_hint = relative_path.parts[0].lower() if len(relative_path.parts) > 1 else None
        language_hint = inferred_hint if inferred_hint in {"en", "si", "ta", "auto"} else default_language_hint

        samples.append(
            BenchmarkSample(
                sample_id=relative_path.with_suffix("").as_posix(),
                audio_path=audio_path,
                reference_path=reference_path,
                language_hint=language_hint,
            )
        )

    return samples


def run_asr_benchmark(
    *,
    provider_name: str,
    provider: SpeechTranscriptionProvider,
    samples: list[BenchmarkSample],
    normalized_output_dir: Path | None = None,
    sample_rate_hz: int = 16000,
    channels: int = 1,
) -> BenchmarkReport:
    results: list[BenchmarkSampleResult] = []

    for sample in samples:
        audio_path = sample.audio_path
        if normalized_output_dir is not None:
            normalized_audio_path = normalized_output_dir / f"{sample.sample_id.replace('/', '_')}.wav"
            audio_path = normalize_audio_to_wav(
                source_path=sample.audio_path,
                target_path=normalized_audio_path,
                sample_rate_hz=sample_rate_hz,
                channels=channels,
            )

        start_time = time.perf_counter()
        transcription = provider.transcribe(audio_path, sample.language_hint)
        elapsed_seconds = time.perf_counter() - start_time

        reference_text = sample.reference_path.read_text(encoding="utf-8")
        hypothesis_text = " ".join(segment.text for segment in transcription.segments).strip()
        duration_seconds = transcription.duration_seconds or 0.0

        results.append(
            BenchmarkSampleResult(
                sample_id=sample.sample_id,
                audio_path=str(sample.audio_path),
                language_hint=sample.language_hint,
                dominant_language=transcription.dominant_language,
                transcription=hypothesis_text,
                wer=compute_word_error_rate(reference_text, hypothesis_text),
                cer=compute_character_error_rate(reference_text, hypothesis_text),
                duration_seconds=duration_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        )

    mean_wer = sum(result.wer for result in results) / len(results) if results else 0.0
    mean_cer = sum(result.cer for result in results) / len(results) if results else 0.0
    realtime_factors = [
        result.elapsed_seconds / result.duration_seconds
        for result in results
        if result.duration_seconds > 0
    ]
    mean_realtime_factor = sum(realtime_factors) / len(realtime_factors) if realtime_factors else 0.0

    return BenchmarkReport(
        provider=provider_name,
        sample_count=len(results),
        mean_wer=mean_wer,
        mean_cer=mean_cer,
        mean_realtime_factor=mean_realtime_factor,
        samples=results,
    )


def compute_word_error_rate(reference_text: str, hypothesis_text: str) -> float:
    reference_words = normalize_metric_text(reference_text).split()
    hypothesis_words = normalize_metric_text(hypothesis_text).split()
    return _error_rate(reference_words, hypothesis_words)


def compute_character_error_rate(reference_text: str, hypothesis_text: str) -> float:
    reference_chars = list(normalize_metric_text(reference_text))
    hypothesis_chars = list(normalize_metric_text(hypothesis_text))
    return _error_rate(reference_chars, hypothesis_chars)


def normalize_metric_text(text: str) -> str:
    return " ".join(text.lower().split())


def _error_rate(reference_items: list[str], hypothesis_items: list[str]) -> float:
    if not reference_items:
        return 0.0 if not hypothesis_items else 1.0

    return levenshtein_distance(reference_items, hypothesis_items) / len(reference_items)


def levenshtein_distance(reference_items: list[str], hypothesis_items: list[str]) -> int:
    if not reference_items:
        return len(hypothesis_items)
    if not hypothesis_items:
        return len(reference_items)

    previous_row = list(range(len(hypothesis_items) + 1))
    for reference_index, reference_item in enumerate(reference_items, start=1):
        current_row = [reference_index]
        for hypothesis_index, hypothesis_item in enumerate(hypothesis_items, start=1):
            insert_cost = current_row[hypothesis_index - 1] + 1
            delete_cost = previous_row[hypothesis_index] + 1
            replace_cost = previous_row[hypothesis_index - 1] + (reference_item != hypothesis_item)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]

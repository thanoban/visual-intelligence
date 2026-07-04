from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Allow `python .\backend\scripts\benchmark_asr.py ...` from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import get_settings
from backend.app.services.asr import build_transcription_provider
from backend.app.services.benchmarking import build_benchmark_samples, run_asr_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local ASR benchmark harness.")
    parser.add_argument("--samples-dir", required=True, help="Directory containing audio files and matching .txt transcripts.")
    parser.add_argument("--provider", choices=["mock", "whisper", "hf"], help="Override ASR_PROVIDER for this run.")
    parser.add_argument("--default-language-hint", choices=["auto", "en", "si", "ta"], default=None)
    parser.add_argument("--output", help="Optional path to write the JSON report.")
    parser.add_argument(
        "--normalize-audio",
        action="store_true",
        help="Normalize each sample to 16kHz mono WAV before transcription.",
    )
    args = parser.parse_args()

    base_settings = get_settings()
    settings = base_settings.model_copy(
        update={"asr_provider": args.provider} if args.provider else {}
    )
    provider = build_transcription_provider(settings)
    samples = build_benchmark_samples(
        Path(args.samples_dir),
        default_language_hint=args.default_language_hint,
    )
    report = run_asr_benchmark(
        provider_name=settings.asr_provider,
        provider=provider,
        samples=samples,
        normalized_output_dir=Path(args.samples_dir) / ".normalized" if args.normalize_audio else None,
        sample_rate_hz=settings.normalized_audio_sample_rate_hz,
        channels=settings.normalized_audio_channels,
    )

    report_json = report.to_json()
    print(report_json)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_json, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

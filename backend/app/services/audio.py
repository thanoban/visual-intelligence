from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import get_settings


class MeetingAudioNormalizer:
    def normalize_meeting_audio(self, relative_audio_path: str) -> str:
        raise NotImplementedError


class NoOpMeetingAudioNormalizer(MeetingAudioNormalizer):
    def normalize_meeting_audio(self, relative_audio_path: str) -> str:
        return relative_audio_path


class StorageBackedMeetingAudioNormalizer(MeetingAudioNormalizer):
    def __init__(self, root: Path, sample_rate_hz: int, channels: int) -> None:
        self.root = root.resolve()
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels

    def normalize_meeting_audio(self, relative_audio_path: str) -> str:
        source_path = (self.root / relative_audio_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source_path}")

        target_path = source_path.parent / "normalized.wav"
        normalize_audio_to_wav(
            source_path=source_path,
            target_path=target_path,
            sample_rate_hz=self.sample_rate_hz,
            channels=self.channels,
        )
        return str(target_path.relative_to(self.root).as_posix())


def normalize_audio_to_wav(
    *,
    source_path: Path,
    target_path: Path,
    sample_rate_hz: int,
    channels: int,
) -> Path:
    source_path = source_path.resolve()
    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if source_path == target_path and source_path.suffix.lower() == ".wav":
        return target_path

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        result = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-i",
                str(source_path),
                "-ar",
                str(sample_rate_hz),
                "-ac",
                str(channels),
                "-c:a",
                "pcm_s16le",
                str(target_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg normalization failed: {result.stderr.strip() or result.stdout.strip()}")
        return target_path

    if source_path.suffix.lower() == ".wav":
        shutil.copy2(source_path, target_path)
        return target_path

    raise RuntimeError("ffmpeg is required to normalize non-WAV audio inputs")


def get_meeting_audio_normalizer() -> MeetingAudioNormalizer:
    settings = get_settings()
    if settings.asr_provider == "mock":
        return NoOpMeetingAudioNormalizer()

    return StorageBackedMeetingAudioNormalizer(
        root=settings.storage_path(),
        sample_rate_hz=settings.normalized_audio_sample_rate_hz,
        channels=settings.normalized_audio_channels,
    )

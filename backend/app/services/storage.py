from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile

from ..config import get_settings


class LocalStorageService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save_meeting_upload(
        self,
        workspace_id: str,
        meeting_id: str,
        upload_file: UploadFile,
    ) -> str:
        meeting_dir = self.root / "workspaces" / workspace_id / "meetings" / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(upload_file.filename or "meeting-upload.bin").name
        target_path = meeting_dir / filename

        with target_path.open("wb") as output_file:
            shutil.copyfileobj(upload_file.file, output_file)

        return str(target_path.relative_to(self.root).as_posix())

    def delete_relative_path(self, relative_path: str | None) -> None:
        if not relative_path:
            return

        target_path = (self.root / relative_path).resolve()
        if not str(target_path).startswith(str(self.root)):
            return

        if target_path.is_file():
            target_path.unlink(missing_ok=True)
            self._cleanup_empty_parents(target_path.parent)

    def delete_meeting_artifacts(self, workspace_id: str, meeting_id: str) -> None:
        meeting_dir = (self.root / "workspaces" / workspace_id / "meetings" / meeting_id).resolve()
        if not str(meeting_dir).startswith(str(self.root)) or not meeting_dir.exists():
            return

        shutil.rmtree(meeting_dir, ignore_errors=True)
        self._cleanup_empty_parents(meeting_dir.parent)

    def resolve_relative_path(self, relative_path: str) -> Path:
        return (self.root / relative_path).resolve()

    def _cleanup_empty_parents(self, directory: Path) -> None:
        current = directory.resolve()
        while current != self.root and current.exists():
            if any(current.iterdir()):
                break
            current.rmdir()
            current = current.parent


def get_storage_service() -> LocalStorageService:
    settings = get_settings()
    return LocalStorageService(settings.storage_path())

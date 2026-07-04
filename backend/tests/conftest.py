from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import get_settings
from backend.app.db import Base, get_db
from backend.app.main import create_app
from backend.app.models import entities as _entities  # noqa: F401
from backend.app.services.audio import NoOpMeetingAudioNormalizer
from backend.app.services.llm import MockLlmProvider
from backend.app.services.mock_providers import MockTranscriptionProvider
from backend.app.services.orchestrator import BackgroundProcessingOrchestrator, RecordingProcessingOrchestrator, get_processing_orchestrator
from backend.app.services.pipeline import FailOnceStageFailureInjector, PipelineProcessor
from backend.app.services.storage import LocalStorageService, get_storage_service


def _build_test_client(tmp_path: Path, *, use_processing_pipeline: bool) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    SessionTesting = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    storage_service = LocalStorageService(tmp_path / "storage")
    failure_injector = FailOnceStageFailureInjector()

    if use_processing_pipeline:
        processor = PipelineProcessor(
            session_factory=SessionTesting,
            transcription_provider=MockTranscriptionProvider(),
            llm_provider=MockLlmProvider(),
            failure_injector=failure_injector,
            audio_normalizer=NoOpMeetingAudioNormalizer(),
        )
        orchestrator = BackgroundProcessingOrchestrator(processor=processor)
    else:
        orchestrator = RecordingProcessingOrchestrator()

    settings = get_settings()
    original_storage_dir = settings.storage_dir
    original_secret_key = settings.app_secret_key
    settings.storage_dir = str(tmp_path / "storage")
    settings.app_secret_key = "test-secret"

    def override_db():
        db = SessionTesting()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_processing_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_storage_service] = lambda: storage_service

    try:
        with TestClient(app) as test_client:
            test_client.recording_orchestrator = orchestrator  # type: ignore[attr-defined]
            test_client.storage_service = storage_service  # type: ignore[attr-defined]
            test_client.failure_injector = failure_injector  # type: ignore[attr-defined]
            test_client.testing_session_factory = SessionTesting  # type: ignore[attr-defined]
            yield test_client
    finally:
        app.dependency_overrides.clear()
        settings.storage_dir = original_storage_dir
        settings.app_secret_key = original_secret_key
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    yield from _build_test_client(tmp_path, use_processing_pipeline=False)


@pytest.fixture()
def processing_client(tmp_path: Path) -> TestClient:
    yield from _build_test_client(tmp_path, use_processing_pipeline=True)

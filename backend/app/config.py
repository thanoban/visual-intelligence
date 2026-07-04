from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./visualsprint.db"
    storage_dir: str = "./storage"
    app_secret_key: str = "visualsprint-dev-secret"
    auth_token_ttl_seconds: int = 60 * 60 * 12

    asr_provider: str = "mock"  # mock | whisper | hf
    llm_provider: str = "mock"  # mock | claude | claude_vertex

    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-4-8"
    llm_max_output_tokens: int = 4000
    llm_chunk_window_seconds: int = 900
    llm_chunk_overlap_seconds: int = 120
    llm_effort: str = "high"

    # Google Cloud Vertex AI (llm_provider=claude_vertex). Auth uses application
    # default credentials: `gcloud auth application-default login`.
    vertex_project_id: str = ""
    vertex_region: str = "global"

    # Per-language ASR model routing. Sinhala/Tamil use community fine-tunes
    # until our own fine-tuned checkpoints replace them.
    asr_model_en: str = "openai/whisper-large-v3"
    asr_model_si: str = "Lingalingeswaran/whisper-small-sinhala"
    asr_model_ta: str = "vasista22/whisper-tamil-medium"

    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()

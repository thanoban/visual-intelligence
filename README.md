# Meeting Intelligence (VisualSprint)

AI-powered screen-aware meeting intelligence that transforms engineering discussions into actionable, evidence-backed workflows.

This repository is the implementation workspace for the multilingual AI meeting assistant described in the planning docs under [`docs/`](./docs).

## Repository layout

- `backend/` - FastAPI API service and future worker-side pipeline code
- `frontend/` - Next.js app placeholder for the MVP web client
- `docs/` - product, scope, architecture, integration, and build plans

## Epic 0 status

The repository now includes a runnable FastAPI entrypoint, a health endpoint, a backend test, local environment scaffolding, and Docker Compose for PostgreSQL.

## Epic 1 progress

The initial SQLAlchemy domain model is now in place for workspaces, users, invites, meetings, transcript segments, analyses, action items, drafts, integrations, job runs, and audit events.

The backend API now includes:

- sign-up, sign-in, and session endpoints
- workspace member invites and invite acceptance
- meeting upload, list, detail, delete, and reprocess endpoints
- local file storage for uploaded recordings
- a no-op processing orchestrator interface that keeps request handlers separate from background execution

## Epic 2 progress

The in-process mock pipeline now runs behind the orchestrator interface and can take a meeting from `uploaded` to `completed` with deterministic transcript segments, summaries, decisions, action items, Jira drafts, Slack drafts, and job-run history.

## Epic 3 progress

The backend now has a configurable meeting LLM provider layer with:

- a real Anthropic Claude provider path
- a Vertex AI Claude provider path
- transcript chunking with overlap for long analyses
- an ask-the-meeting chat endpoint with cited transcript segments
- smoke tests that auto-skip when live SDK credentials are not present

## Epic 4 progress

The backend now includes:

- ASR provider abstraction for `mock`, local `faster-whisper`, and routed Hugging Face Whisper checkpoints
- language routing that keeps English on the local Whisper baseline and reroutes Sinhala/Tamil to configured Hugging Face checkpoints
- ingest-time audio normalization plumbing for real ASR paths
- a local benchmark harness at `backend/scripts/benchmark_asr.py` that measures WER, CER, and realtime factor from a folder of audio plus matching transcript files

## Run locally

1. Create a virtual environment and install backend dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r .\backend\requirements.txt
   ```

   For real transcription providers, also install:

   ```powershell
   pip install -r .\backend\requirements-asr.txt
   ```

2. Copy the backend environment template:

   ```powershell
   Copy-Item .\backend\.env.example .\backend\.env
   ```

3. Start PostgreSQL if you want a local database service:

   ```powershell
   docker compose up -d db
   ```

4. Run the API:

   ```powershell
   uvicorn backend.app.main:app --reload
   ```

5. Verify the health endpoint:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```

## Test command

Run the backend test suite with:

```powershell
python -m pytest .\backend\tests
```

## Benchmark command

Run the ASR benchmark harness on a sample folder where each audio file has a matching `.txt` transcript with the same basename:

```powershell
python .\backend\scripts\benchmark_asr.py --samples-dir .\eval\en --provider whisper
```

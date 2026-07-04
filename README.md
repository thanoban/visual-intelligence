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

## Run locally

1. Create a virtual environment and install backend dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r .\backend\requirements.txt
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

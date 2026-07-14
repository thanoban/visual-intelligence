# 10 - Platform Foundations

This document explains the base technical shape of the current VisualSprint codebase. Read this first if you want to understand why the project is organized the way it is before you dive into individual features.

## 1. What this project is at code level

VisualSprint is a monorepo with two active runtime applications:

- `backend/` is a FastAPI service that owns authentication, authorization, persistence, meeting upload, background processing, analysis, drafts, and question answering.
- `frontend/` is a Next.js App Router application that owns sign-in, meeting review, transcript playback, draft review, chat, and workspace settings.

The docs folder now has two kinds of documents:

- planning documents (`01` through `08` plus `CORRECTIONS`) that explain product, architecture, and roadmap
- implementation guides (`10` onward) that explain how the real code works

## 2. Core technology choices and why they fit

### FastAPI

FastAPI is used because the backend needs a compact HTTP layer with:

- clear request and response models
- easy dependency injection
- good async-compatible lifecycle hooks
- automatic OpenAPI docs

In this repo the routes stay intentionally thin. They validate inputs, load the current user, call services, and serialize responses.

### SQLAlchemy ORM

SQLAlchemy is the persistence layer because the domain model is relational:

- workspaces own users, invites, meetings, integrations, and audit events
- meetings own transcript segments, analyses, action items, drafts, and job runs

The ORM keeps those relationships explicit in `backend/app/models/entities.py`, and that makes the rest of the code read in terms of domain objects instead of manual SQL strings.

### Pydantic

Pydantic is used in two different ways:

1. API schemas: request and response payload validation
2. LLM schemas: structured output validation for Claude responses

That second use is especially important. The LLM code does not parse loose free text. It asks Claude for responses that match explicit schema objects, then validates them before the rest of the system trusts them.

### Next.js App Router with TypeScript

The frontend needs:

- page routing
- client-side state for interactive meeting review
- typed API contracts
- a build step that catches React and TypeScript mistakes early

The App Router structure also maps nicely to the product surface:

- `/sign-in`
- `/sign-up`
- `/invite`
- `/meetings`
- `/meetings/[meetingId]`
- `/settings`

### Local disk + SQLite in the current milestone

The current code is optimized for local development and deterministic testing:

- SQLite keeps setup light
- local disk storage keeps upload and deletion logic easy to trace
- mock ASR and mock LLM providers keep tests offline and stable

This is not the final production topology. The seams are already prepared for PostgreSQL, queue workers, and external storage.

## 3. How the backend boots

Read these files in order:

1. `backend/app/main.py`
2. `backend/app/config.py`
3. `backend/app/db.py`
4. `backend/app/api/router.py`

### `main.py`

`create_app()` builds the FastAPI application and wires:

- app metadata
- the lifespan hook
- CORS middleware
- the aggregated router

The lifespan hook currently calls `init_db()`, which runs `Base.metadata.create_all(...)`. That is convenient for local work, but the docs correctly note that a migration system is still needed before production data.

### `config.py`

`Settings` extends `BaseSettings`, so environment variables become typed configuration fields. A few important ideas are embedded here:

- the project can switch providers by configuration, not by code edits
- the backend can keep safe local defaults
- expensive or external integrations are optional until enabled

`get_settings()` is wrapped in `@lru_cache`, so the config object behaves like a shared singleton during a process lifetime.

### `db.py`

`db.py` creates:

- a SQLAlchemy engine
- a session factory
- the declarative base
- the request-scoped `get_db()` dependency

SQLite gets `check_same_thread=False` because background processing and request handling can touch the same database file in the current one-process development setup.

## 4. The dependency injection pattern

FastAPI dependencies are one of the most important patterns in this repo.

Examples:

- `get_db()` provides a database session to routes
- `get_current_user()` turns a bearer token into a verified `User`
- `get_storage_service()` returns the storage implementation
- `get_processing_orchestrator()` returns the processing implementation
- `get_meeting_llm_provider()` returns the active LLM implementation
- `get_transcription_provider()` returns the active ASR implementation

This is why the project stays testable. Tests can override these dependencies and swap in mocks or controlled implementations without editing application code.

## 5. How the project separates responsibilities

The codebase repeatedly uses the same separation pattern:

### Routes

Files under `backend/app/api/routes/` own HTTP concerns:

- parsing user input
- status codes
- authentication requirements
- request-specific error messages

They should not carry deep business logic.

### Services

Files under `backend/app/services/` own domain behavior and infrastructure seams:

- pipeline logic
- provider logic
- storage behavior
- audio normalization
- orchestration behavior

### Schemas

Files under `backend/app/schemas/` define request and response contracts. These are what the API promises externally.

### Serializers

`backend/app/serializers.py` converts ORM entities into response schemas. This keeps route code from building JSON objects manually.

### Models

`backend/app/models/entities.py` is the canonical domain map. When you want to understand the real data model, start there.

## 6. How the frontend is organized

The frontend uses three layers:

### Pages

Files under `frontend/src/app/` define route entry points.

### Components

Files under `frontend/src/components/` carry reusable UI and stateful behavior:

- `session-provider.tsx`
- `meeting-upload-form.tsx`
- `transcript-player.tsx`
- `draft-queue.tsx`
- `chat-panel.tsx`
- `app-shell.tsx`

### Client library

`frontend/src/lib/` holds:

- `api.ts` for HTTP calls
- `types.ts` for typed contracts
- `format.ts` for display formatting helpers

The frontend does not invent a second domain model. It consumes the backend contracts directly through typed interfaces.

## 7. The current runtime topology

Today:

- the API process handles HTTP requests
- background tasks run meeting processing in-process
- SQLite stores application data
- local disk stores uploaded media

That means the current build is easy to inspect, but it also means:

- API restarts can disrupt in-flight work
- there is no durable queue yet
- scaling is intentionally limited

The code prepares for a future where:

- API only enqueues work
- workers process jobs separately
- PostgreSQL stores tenant data
- object storage stores artifacts

## 8. How to read this codebase efficiently

When learning a feature, use this reading order:

1. route file
2. schema file
3. serializer file
4. service file
5. ORM entity definitions
6. frontend API function
7. frontend page/component that uses it
8. backend test covering the flow

That order mirrors how the system actually behaves at runtime.

## 9. Important design principles used repeatedly

### Workspace scoping everywhere

The project treats workspace ownership as a first-class security boundary. Most meeting routes do not fetch by `meeting_id` alone. They fetch by meeting id inside the current user's workspace.

### Seams before scale

Even when the implementation is simple today, the interface is designed for future replacement. That is why there is already a storage service, provider factories, and an orchestrator interface.

### Structured output over text scraping

The LLM layer is built on typed schemas. That reduces fragile downstream parsing.

### Deterministic mocks first

The test suite prefers local, deterministic provider behavior. That makes feature development faster and safer.

## 10. What to read next

After this guide, continue in this order:

1. `11-AUTH-WORKSPACE-AND-INVITES.md`
2. `12-MEETING-INGEST-AND-PIPELINE.md`
3. `13-ANALYSIS-DRAFTS-AND-CHAT.md`
4. `14-FRONTEND-APP-FLOWS.md`
5. `15-TESTING-AND-DEBUGGING.md`

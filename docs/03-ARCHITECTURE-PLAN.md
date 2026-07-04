# 03 — Architecture Plan

High-level technical design for the coding agent. This is a specification — no source code here. Naming, exact schemas, and framework idioms are the builder's choice as long as the behavior and structure below are preserved.

## Stack decisions

| Layer | Choice | Reason |
|---|---|---|
| Backend API | Python + FastAPI | Best ecosystem fit for ASR/ML (Hugging Face, Whisper) and the Anthropic SDK; async-friendly |
| Background processing | Queue-based worker (Redis + a Python task queue such as ARQ/Celery/Dramatiq — builder's choice) | Meeting processing is minutes-long; must never run inside a request handler. For the very first local milestone, in-process background tasks are acceptable behind the same orchestrator interface, swapped for the queue before deployment |
| Database | PostgreSQL (SQLite acceptable for local dev via the same ORM) | Relational fits meetings/segments/items; SQLAlchemy 2.x as ORM |
| Object storage | Local disk in dev; S3-compatible bucket in production | Audio files and artifacts |
| Frontend | Next.js (React, TypeScript, App Router) | Standard, hireable, good DX |
| LLM | Claude via the official Anthropic Python SDK | Provider-switchable: Anthropic API or Google Vertex AI (see LLM layer) |
| ASR | Pluggable providers with per-language routing | See ASR layer and the Language Strategy doc |
| Deployment | Docker Compose for dev; single cloud VM or container service for first production | Keep ops trivial until traction |

## System components

1. **Web app (Next.js)** — auth, meeting list, meeting detail (player + synced transcript + summaries + action items + draft queue + chat), settings (integrations, language defaults, Slack channel).
2. **API service (FastAPI)** — REST endpoints, auth/session handling, workspace authorization, enqueue of processing jobs, webhook receivers (bot-provider callbacks, Jira/Slack OAuth callbacks).
3. **Worker** — consumes processing jobs, runs the pipeline stages (below), writes results to the database, emits status updates.
4. **Providers** — ASR provider layer, LLM provider layer, integration clients (bot API, Jira, Slack, Google Calendar). All behind interfaces with mock implementations for tests.

## Processing pipeline (the heart of the product)

A meeting moves through explicit, resumable stages. Each stage is idempotent, records its status and timing, and can be retried independently. Statuses visible to users: uploaded → processing → completed / failed.

1. **Ingest** — store the audio (from bot recording callback or upload), normalize to a standard audio format, probe duration.
2. **Transcribe** — route to an ASR provider by language hint or automatic language detection; output timestamped segments with per-segment language tags.
3. **Diarize (post-MVP flag)** — assign speaker labels; MVP may rely on ASR/channel heuristics and bot-provided speaker events, with a dedicated diarization model added later. The data model must carry speaker labels from day one.
4. **Analyze** — one structured-extraction call to the LLM provider returning: original-language summary, English summary, key points, decisions, action items (text, owner, due, evidence segment references). The response must be schema-validated (structured outputs), never free-text parsed.
5. **Draft** — build Jira issue drafts from action items and a Slack summary message draft. Drafts are stored with status draft; nothing is sent externally in this stage.
6. **Notify** — if the workspace enables auto-post, send the Slack summary; otherwise leave for manual send.

Failure policy: each stage retries with backoff a bounded number of times; a stage that exhausts retries marks the meeting failed with a stored, human-readable reason; the UI offers reprocessing from the failed stage.

## ASR layer

- A provider interface: input is an audio file path plus an optional language hint; output is a list of segments (start seconds, end seconds, speaker label, text, language) plus detected dominant language and duration.
- Implementations:
  - **Mock** — deterministic canned output, used by all tests and local dev without GPUs.
  - **Whisper (local)** — faster-whisper multilingual large model for English and auto-detected languages.
  - **Hugging Face fine-tunes (routed)** — per-language model routing driven by configuration: English → Whisper large; Tamil → the vasista22 Tamil Whisper family; Sinhala → the best community Sinhala Whisper fine-tune, later replaced by our own fine-tuned checkpoint. See the Language Strategy doc for candidates and evaluation.
- Routing rule: explicit user hint wins; otherwise detect language on a sample window, then run the routed model. Mixed-language meetings use the multilingual model with the code-switch behavior evaluated in the benchmark.
- ASR runs on the worker, not the API process. Model weights load once per worker process and are reused.

## LLM layer

- A provider interface with two operations: analyze-meeting (transcript in → validated analysis object out) and answer-question (transcript + question in → answer text + cited segment references out).
- Implementations:
  - **Mock** — canned analysis for tests.
  - **Anthropic API** — official Python SDK, model configurable, default claude-opus-4-8, adaptive thinking enabled, structured outputs (the SDK's parse/validated-schema mechanism) for the analysis object.
  - **Vertex AI** — the SDK's Vertex client (same request surface, bare model IDs, Google application-default credentials, project and region from configuration). Chosen purely by configuration; no code paths outside the provider layer may know which backend is active.
- Prompting requirements (content, not code): the analysis prompt must state that meetings may mix Sinhala/Tamil/English in the same sentence; instruct extraction only of items actually said; require the English summary regardless of spoken language; require owner attribution only when a name is stated or clearly implied; require evidence segment references for every decision and action item.
- Long transcripts: chunk by time windows with overlap, analyze per chunk, then merge in a final consolidation call. Token budgets and chunk sizes are configuration values.

## Data model (entities and key fields, described)

| Entity | Key fields (beyond id/timestamps) | Notes |
|---|---|---|
| Workspace | name, settings (default language hint, Slack channel, auto-post flag) | Tenant boundary; every query is workspace-scoped |
| User | email, name, role (owner/member) | Belongs to one workspace in MVP |
| Meeting | workspace, title, source (bot/upload), status, language hint, detected language, duration, audio object key, error reason | Status transitions per pipeline |
| TranscriptSegment | meeting, index, start/end seconds, speaker label, text, language tag | Ordered; the citation unit |
| MeetingAnalysis | meeting, summary (original language), summary (English), key points, decisions | Decisions carry evidence segment references |
| ActionItem | meeting, text, owner name, owner user (nullable), due date (nullable), evidence segment references, state (open/dismissed/exported) | |
| Draft | meeting, action item (nullable for the Slack draft), kind (jira issue / slack message), payload (structured content), status (draft/approved/sent/dismissed), external reference (Jira key / Slack message id), acted-by user, acted-at | The approval queue |
| IntegrationConnection | workspace, provider (jira/slack/google), OAuth tokens (encrypted), provider-side identifiers (Jira site and project, Slack channel) | Secrets never in logs |
| JobRun | meeting, stage, attempt, status, started/finished, error | Pipeline observability |
| AuditEvent | workspace, actor, action, target, timestamp | Approvals, deletions, exports |

## API surface (behavioral description)

- Auth: sign-up, sign-in, session (cookie or token — builder's choice), invite member.
- Meetings: create-by-upload (multipart), list (workspace-scoped, paginated), detail (segments, analysis, action items, drafts), delete (cascades storage), reprocess.
- Chat: ask a question about one meeting; response includes answer text and cited segment ids.
- Drafts: list per meeting, edit payload, approve (triggers Jira create or Slack post), dismiss.
- Integrations: start OAuth for Jira/Slack/Google Calendar, callback handlers, connection status, disconnect.
- Webhooks: bot-provider events (recording ready, meeting ended) — verified by signature.
- Health/readiness endpoints for ops.
- All meeting-scoped routes enforce workspace membership; no cross-tenant access.

## Security and privacy requirements

- Recording consent: the bot announces itself by name ("VisualSprint notetaker"); workspace setting for a spoken/chat consent notice where required.
- Encrypt integration tokens at rest; never log tokens, transcripts, or audio URLs.
- Deletion is real: removing a meeting deletes audio, segments, analysis, drafts, and vector/index artifacts if any.
- Configurable retention (delete audio after N days, keep transcript) is a fast-follow; design the storage layer so it is easy.
- Rate-limit auth and chat endpoints.

## Scalability path (do not build ahead of need, but do not block it)

- Stateless API and worker processes → horizontal scale behind a load balancer.
- Queue depth is the scaling signal for workers; ASR workers (GPU) scale separately from analysis workers (API-bound).
- Postgres first; read replicas and object-storage lifecycle rules later.
- Multi-workspace-per-user, SSO, and audit exports are Phase 5 — the data model above does not preclude them.

## Existing scaffold note

A partial backend scaffold already exists under the backend directory (requirements files, environment example, configuration and database session modules). The builder may keep, extend, or regenerate it — the specification in this document is authoritative, not those files.

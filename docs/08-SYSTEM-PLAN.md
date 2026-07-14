# 08 — Full System Plan

Authoritative description of the VisualSprint system: how the pieces fit, how data moves, where the seams are, and how it runs today versus at scale. This is grounded in the current build (Epics 0–3) and extends to the full target. It is the reference for system topology; doc 03 remains the architecture rationale, doc 02 the behavioral spec, doc 07 the roadmap/status. No code here — descriptions and diagrams only.

## 1. System at a glance

VisualSprint is a multi-tenant web application with an asynchronous media-processing core. A team uploads (or a bot delivers) a meeting recording; the system transcribes it in the team's language, has an LLM extract structured meaning, turns that meaning into reviewable Jira and Slack drafts, and lets the team ask questions of the meeting with cited answers.

```
   Browser (Next.js)                External services
        |                        (Claude API / Vertex AI,
        | HTTPS/JSON              Jira, Slack, Google Calendar,
        v                         bot provider, Hugging Face models)
  +-----------+   enqueue   +-----------+   read/write   +-----------+
  |  API      |------------>|  Worker   |<-------------->| Providers |
  | (FastAPI) |             | (pipeline)|                | (ASR/LLM/ |
  +-----+-----+             +-----+-----+                | integr.)  |
        |                         |                      +-----------+
        |  SQL                    |  SQL / files
        v                         v
  +----------------+       +----------------+
  |  PostgreSQL    |       | Object storage |
  | (tenant data)  |       | (audio/artifacts)
  +----------------+       +----------------+
```

Today the API and worker run in one process (background tasks) against SQLite and local disk. The target separates them into independent processes against PostgreSQL, a queue, and object storage — the code seams for that split already exist.

## 2. Components

| Component | Responsibility | Current state |
|---|---|---|
| Web app (Next.js) | Auth screens, meeting list, meeting detail (player + synced transcript + summaries + decisions + action items + draft queue + chat), settings | Not started (Epic 5) |
| API service (FastAPI) | HTTP endpoints, auth, workspace authorization, upload handling, enqueue, later the OAuth callbacks and provider webhooks | Built: auth, workspace, meeting CRUD, chat |
| Worker / pipeline | Runs the staged processing pipeline, writes results, records job runs | Built as an in-process background runner behind an orchestrator interface |
| Provider layer | ASR, LLM, and integration clients, each behind an interface with a mock | LLM (mock/Anthropic/Vertex) and transcription (mock) built; real ASR and integrations pending |
| PostgreSQL | All tenant and pipeline data | Modeled; runs on SQLite in dev, Postgres available via compose |
| Object storage | Audio uploads and derived artifacts | Local-disk implementation behind a storage service interface |
| Queue + Redis | Decouple enqueue from execution | Pending (Epic 6) |

## 3. Module map (backend, as built)

| Area | Modules | Purpose |
|---|---|---|
| Entry / wiring | `app/main.py`, `app/api/router.py` | App factory, CORS, lifespan schema init, route aggregation |
| Config | `app/config.py` | Single settings object (env-driven) for database, storage, provider selection, model routing, LLM tuning, Vertex, auth |
| Persistence | `app/db.py`, `app/models/entities.py` | Engine/session, declarative base, all ORM entities and enums |
| Auth | `app/security.py`, `app/dependencies.py` | PBKDF2 password hashing, HMAC-signed bearer tokens, current-user dependency binding user to workspace |
| API routes | `app/api/routes/` (auth, workspace, meetings, health) | HTTP surface |
| Schemas / serializers | `app/schemas/`, `app/serializers.py` | Request/response models and entity-to-response mapping |
| Services | `app/services/` (storage, orchestrator, pipeline, llm, mock_providers) | Storage seam, enqueue seam, staged pipeline, LLM provider layer, mock ASR/LLM |
| Tests | `backend/tests/` | Health, schema, auth+meetings, LLM, mock pipeline; live-provider tests skip without credentials |

## 4. Runtime processes and how they run

**Current (development / first milestone):**
- One process: the FastAPI app. Meeting processing runs inside it via background tasks after the upload request returns. Data in SQLite; audio on local disk. This is deliberately simple and is the demo/dev configuration.

**Target (design-partner and beyond):**
- **Web** process serving the Next.js app.
- **API** process(es), stateless, behind a load balancer; only enqueue work, never run the pipeline inline.
- **Worker** process(es) consuming from the queue and running the pipeline. Two worker classes eventually: ASR workers (heavy, possibly GPU) and analysis/integration workers (API-bound), scaled independently.
- **PostgreSQL**, **Redis** (queue), and **object storage** as backing services.

The orchestrator interface (enqueue a meeting) and the pipeline processor (run the stages) are already separate objects, so moving from background tasks to a queue is a swap of the orchestrator implementation, not a rewrite.

## 5. Primary data flows

### 5.1 Upload → processed meeting

1. Authenticated user posts a file to the upload endpoint with an optional title and language hint.
2. API creates a meeting record (status uploaded), stores the audio via the storage service under a workspace/meeting path, saves the returned object key, and asks the orchestrator to enqueue the meeting.
3. The pipeline runs its stages in order — ingest → transcribe → analyze → draft — each stage recording a job run (attempt, status, timing, error) and retrying with backoff up to a bounded number of attempts.
4. On success the meeting becomes completed with transcript segments, an analysis (both summaries, key points, decisions), action items, and one Jira draft per action item plus one Slack draft. On exhausted retries the meeting becomes failed with a human-readable reason.
5. Reprocessing resumes from the failed stage, clearing only the outputs from that stage forward, so a late-stage failure does not redo transcription.

### 5.2 Ask-the-meeting

1. User posts a question to a meeting's chat endpoint.
2. API confirms workspace ownership and that transcript segments exist, then calls the LLM provider's answer operation with the meeting title, segments, and question.
3. The provider returns an answer, cited segment ids, and a not-discussed flag; the API maps cited ids back to segment details (timestamps, speaker, text) and returns them so the UI can jump the player to each citation.

### 5.3 Draft approval (target, Epics 7–8)

1. User reviews the draft queue on the meeting page, edits payloads as needed.
2. Approving a Slack draft posts the summary to the configured channel; approving a Jira draft creates an issue in the connected project with evidence quotes and an assignee resolved from the owner-to-user link.
3. Each external action is idempotent, stores the external reference on the draft, and records an audit event. Nothing reaches Jira or Slack without approval.

### 5.4 Bot capture (target, Epic 9)

1. Workspace connects Google Calendar; upcoming meetings with video links are discovered.
2. Per auto-join rules, the bot provider is asked to join; the bot announces itself and records.
3. The provider's signed webhook delivers the recording; the API ingests it into the same pipeline as an upload. The upload path stays independent of the bot provider.

## 6. Provider seams (the extension points)

Every external dependency sits behind an interface with a mock, selected by configuration, so the whole system runs and tests offline.

| Seam | Interface shape | Implementations |
|---|---|---|
| Transcription (ASR) | audio path + language hint → segments, dominant language, duration | Mock (built); local Whisper and routed Hugging Face per-language (Epic 4) |
| LLM | analyze-meeting → validated analysis; answer-question → answer + citations | Mock, Anthropic API, Vertex AI (all built) |
| Storage | save/delete/resolve meeting artifacts by workspace and meeting | Local disk (built); S3-compatible (target) |
| Orchestration | enqueue a meeting for processing | In-process background (built); queue-based worker (Epic 6) |
| Integrations | Jira, Slack, Calendar, bot provider clients | Pending (Epics 7–9), each mocked in tests |

The LLM provider selection is the model for the others: one factory reads the configured provider name and returns mock, Anthropic, or Vertex — no caller knows which backend is active. The ASR factory must follow the same pattern when real ASR lands (it currently hardcodes the mock regardless of configuration — see correction C6).

## 7. Data model relationships

Tenancy flows from the workspace; every meeting-scoped query filters by workspace, enforced through the current-user dependency.

```
Workspace 1---* User
Workspace 1---* WorkspaceInvite
Workspace 1---* Meeting
Workspace 1---* IntegrationConnection
Workspace 1---* AuditEvent

Meeting 1---* TranscriptSegment      (the citation unit; unique per index)
Meeting 1---1 MeetingAnalysis        (two summaries, key points, decisions)
Meeting 1---* ActionItem             (owner name + optional owner user + evidence)
Meeting 1---* Draft                  (jira issue / slack message; approval state)
Meeting 1---* JobRun                 (per stage, per attempt: status/timing/error)

ActionItem 1---* Draft               (an action item's Jira draft)
User      1---* ActionItem           (owner_user, when matched)
User      1---* Draft                (who approved)
```

Key design points already in place: cascade deletes from workspace and meeting; a unique transcript segment index per meeting; a one-to-one analysis per meeting; drafts carry the approval lifecycle and external reference; job runs give per-stage observability; the audit table is ready for approvals, deletions, and exports; integration tokens have an encrypted-at-rest column awaiting the integration epics.

## 8. Security model

- **Passwords:** PBKDF2-HMAC-SHA256 with per-user salt and a high iteration count; constant-time verification.
- **Sessions:** stateless bearer tokens carrying user id, workspace id, and expiry, signed with an application secret via HMAC-SHA256 and verified in constant time. Expired or tampered tokens are rejected. (A vetted JWT library is a reasonable future hardening, but the current scheme is sound.)
- **Authorization:** the current-user dependency binds the token's user to its workspace and rejects mismatches; every meeting route resolves the meeting within the caller's workspace, so cross-tenant access returns not-found. A cross-workspace access test exists.
- **Secrets:** integration OAuth tokens are stored in an encrypted column; tokens, transcripts, and audio keys must never be logged. Provider webhooks (bot, Jira, Slack) must be signature-verified.
- **Data lifecycle:** deleting a meeting removes its stored audio and, by cascade, all derived rows. Path handling in the storage service confines operations to the storage root. Configurable retention (delete audio after N days, keep transcript) is a fast-follow the storage seam is designed to accommodate.
- **Transport:** HTTPS in production; CORS origins are configuration-driven.

## 9. Configuration surface

A single settings object, environment-driven, with safe local defaults, controls: database URL; storage directory; auth secret and token lifetime; ASR provider and per-language model ids plus audio-normalization parameters; LLM provider, model, output-token budget, chunk window and overlap, and effort; Vertex project and region; and CORS origins. Provider selection is the primary switch — the same build runs fully mocked, on the Anthropic API, or on Vertex AI purely by changing environment values. Heavy ASR dependencies live in a separate requirements file so the default (mock) install stays light.

## 10. Processing pipeline internals

- **Stages:** ingest (verify stored audio), transcribe (route to ASR, replace segments, set detected language and duration), analyze (chunk the transcript, call the LLM per chunk, consolidate, persist analysis and action items), draft (build one Jira draft per action item and one Slack summary draft). Diarize and notify stages exist as enum placeholders for later epics (speaker diarization; Slack auto-post).
- **Reliability:** each stage is idempotent and clears its own forward outputs before running, so retries and reprocessing never duplicate data. Retries use bounded attempts with short backoff; exhaustion marks the meeting failed with a readable reason and the failing stage.
- **Resumability:** reprocessing detects the last failed stage and restarts there, preserving earlier successful work (notably transcription, the most expensive stage).
- **LLM handling:** analysis and answers use schema-validated structured output (never free-text parsing); long transcripts are split into overlapping time windows, analyzed per window, then merged in a consolidation pass that deduplicates and preserves segment-id evidence.

## 11. Scaling plan

- **Statelessness:** API and worker hold no in-memory session state, so both scale horizontally. The token scheme requires no server-side session store.
- **Queue depth** is the worker scaling signal. ASR and analysis workloads scale separately once split, because their resource profiles differ (GPU/CPU-heavy transcription versus API-latency-bound analysis and integrations).
- **Database:** PostgreSQL first; read replicas and object-storage lifecycle rules later. The schema uses indexed foreign keys on the hot paths (meeting by workspace, segments/items/drafts/job-runs by meeting).
- **Cost controls:** per-meeting ASR and bot-provider costs are tracked from the first real run; the free tier is sized so paid conversion covers processing cost.
- **Headroom for later:** the model does not preclude multi-workspace users, SSO, audit exports, or retention controls — those are additive, not restructuring.

## 12. Observability and operations

- **Job runs** already provide per-stage, per-attempt visibility (status, timing, error) — the backbone for a processing dashboard and for stuck-job detection.
- **Health/readiness** endpoints exist for load-balancer checks.
- **Targeted for hardening (Epic 10):** structured logging (never secrets), error alerting, stuck-job detection (nothing in processing beyond a timeout without a job-run heartbeat), graceful worker shutdown, and a seed/demo script.
- **Schema evolution:** move from create-all bootstrapping to managed migrations before the first deployment with real data (correction C5).

## 13. Environments

| Environment | API + worker | Database | Storage | Providers |
|---|---|---|---|---|
| Local dev / tests | One process, background tasks | SQLite | Local disk | All mock (no keys, no GPU) |
| Demo | One or two processes | SQLite or Postgres | Local disk | Real LLM (Anthropic or Vertex), real or hosted ASR |
| Design-partner production | Separate API and worker processes | PostgreSQL | S3-compatible | Real LLM, real ASR, Jira/Slack/Calendar/bot connected, migrations, HTTPS |

## 14. Known system-level gaps (see CORRECTIONS.md for detail)

- Live Claude calls currently send a sampling parameter the default model rejects (P0, C1) — the single blocker for a real-API demo.
- Output-token budget is likely too low under adaptive thinking and should stream (C2).
- No offline guard test for live-provider call arguments (C3); owner-to-user matching not yet done (C4); schema uses create-all rather than migrations (C5); ASR provider selection not yet wired to configuration (C6); notify/diarize stages not yet run (C7); processing still in-process pending the queue (C8); test run command undocumented and path-sensitive (C9).

None of these change the system shape; they are fixes and the next epics along the plan in doc 07.

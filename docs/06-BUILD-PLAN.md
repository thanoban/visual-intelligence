# 06 — Build Plan (handoff to the coding agent)

Execute epics in order. Every epic ends with passing automated tests and a demonstrable result. Follow the Architecture Plan (doc 03) for structure and the MVP Scope (doc 02) for behavior; where they conflict, MVP Scope wins on behavior, Architecture Plan wins on structure.

## Ground rules for the builder

1. **Mocks first.** ASR and LLM providers must have mock implementations; the entire test suite and local dev run with zero external services, zero GPU, zero API keys.
2. **No stage in a request handler.** Meeting processing always runs in background execution behind the orchestrator interface (in-process runner acceptable for Epic 1–3, queue-based worker required from Epic 6).
3. **Structured LLM output only.** Meeting analysis must come back schema-validated through the Anthropic SDK's structured-output/parse mechanism — never regex/JSON-scrape free text. Default model claude-opus-4-8, adaptive thinking on, model and provider configurable. The Vertex AI variant uses the SDK's Vertex client with the same model id and identical downstream behavior.
4. **Multi-tenant discipline from the first table.** Every meeting-scoped query is filtered by workspace; write at least one test proving cross-workspace access fails.
5. **Secrets hygiene.** Tokens encrypted at rest, never logged; environment-driven configuration with a documented example file.
6. **Definition of done per epic:** code + tests green + a short usage note appended to the project README.

An early partial scaffold exists under the backend directory (requirements, env example, config and db modules). Reuse or replace it; docs 02–05 are authoritative.

## Epic 0 — Repository foundation
- Monorepo layout: backend, frontend, docs; git initialized; ignore rules; environment example files; Docker Compose for Postgres (and Redis when Epic 6 lands); README with run instructions.
- CI-ready test command for the backend (single command runs the full suite).
- *Done when:* fresh clone → documented commands → API health endpoint responds and tests pass.

## Epic 1 — Data model and API skeleton
- Entities from the Architecture Plan data-model table, with migrations.
- Auth (sign-up, sign-in, session), workspace creation, member invite.
- Meeting endpoints: upload (stores file, creates record, enqueues processing), list, detail, delete, reprocess.
- *Done when:* upload returns a meeting in uploaded status; list/detail respect workspace boundaries (tested); delete removes the stored file.

## Epic 2 — Processing pipeline with mock providers
- Orchestrator running the staged pipeline (ingest → transcribe → analyze → draft) with JobRun records, retries with backoff, failure states, and reprocess-from-failed-stage.
- Mock ASR returns a deterministic multilingual transcript; mock LLM returns a deterministic analysis with evidence references.
- *Done when:* an uploaded file reaches completed status with segments, both summaries, decisions, action items, one Jira draft per action item, and a Slack draft — all via mocks; a forced stage failure shows a readable error and can be reprocessed.

## Epic 3 — Real LLM analysis
- Anthropic provider implementing analyze-meeting and answer-question per the Architecture Plan's LLM layer, including the prompting requirements (code-switch awareness, conservative extraction, mandatory English summary, evidence references) and transcript chunking for long meetings.
- Vertex AI variant selected purely by configuration; one smoke test per provider that runs only when credentials are present (skipped otherwise).
- Ask-the-meeting endpoint wired to answer-question with segment citations.
- *Done when:* a real English transcript produces sensible validated analysis; the chat endpoint returns cited answers; provider switch requires only environment changes.

## Epic 4 — Real ASR with language routing
- Whisper-based provider (local) for English/auto; Hugging Face routed provider for Sinhala and Tamil using the configured model ids from the Language Strategy doc; routing rule: user hint wins, else detected language.
- Audio normalization on ingest (any common upload format → the pipeline's standard format).
- A small benchmark harness (separate from the app) that runs any provider against an evaluation folder of audio + reference transcripts and reports WER/CER per language — this harness is a deliverable of the Language Strategy, built here because it shares the provider layer.
- *Done when:* an uploaded English recording produces a real transcript end to end; si/ta recordings route to the configured models; the harness produces a metrics report from a sample folder.

## Epic 5 — Frontend MVP
- Next.js app: auth screens; meeting list with upload; meeting detail with audio player synced to transcript, both summaries, decisions, action items with evidence jump-links, draft review queue (edit/approve/dismiss), chat box with citation jumps; workspace settings (language default, Slack channel placeholder, integration status).
- Clean, professional visual design; responsive enough for laptop use; no mobile app.
- *Done when:* the full demo script in the MVP Scope doc can be walked through against the local backend (with mock or real providers).

## Epic 6 — Queue-based worker and packaging
- Move pipeline execution to the queue-based worker (Redis-backed); API only enqueues. Worker and API run as separate processes in Docker Compose.
- Concurrency limits, graceful shutdown, stuck-job detection (nothing in processing beyond a configurable timeout without a JobRun heartbeat).
- *Done when:* API restart does not lose in-flight meetings; two meetings process concurrently; compose brings up web, api, worker, db, redis with one command.

## Epic 7 — Slack integration
- OAuth connect, channel picker, message formatting per the Integrations Plan, auto/manual posting, idempotent sends, audit events.
- *Done when:* a completed meeting posts a correctly formatted summary to a real Slack workspace; duplicates are impossible on retry.

## Epic 8 — Jira integration
- OAuth connect, project selection, draft approval creates a real issue with correct fields and evidence quotes; assignee matching by email with unassigned fallback; error surfacing keeps the draft editable; audit events.
- *Done when:* the approve flow works against a real Jira Cloud site; dismissed drafts never reach Jira (tested).

## Epic 9 — Bot capture
- Google Calendar OAuth and meeting discovery; bot-provider integration (Recall.ai first): schedule/join per auto-join rules, webhook receiver with signature verification, recording ingestion into the existing pipeline; per-meeting opt-out; provider cost logging per meeting.
- *Done when:* a scheduled Google Meet call is joined by the bot, and the recording appears and processes automatically; upload path remains fully independent.

## Epic 10 — Hardening for design partners
- Retention/deletion guarantees verified end to end; rate limiting; basic observability (structured logs, error alerting); seed/demo data script; deployment to a single cloud host with HTTPS; onboarding notes for the first ten partner teams.
- *Done when:* the founder can onboard a real agency team without developer intervention.

## Test strategy summary
- Unit tests for extraction-adjacent logic (chunking, owner matching, draft building, idempotency keys).
- Pipeline integration tests entirely on mocks (fast, deterministic, run in CI).
- Provider contract tests: mock and real providers satisfy the same interface test suite; real-credential tests auto-skip when secrets are absent.
- One end-to-end happy-path test per epic from Epic 5 onward (upload → completed → drafts → approve with a faked external service).

## Order rationale
English value loop first (Epics 0–5) proves the product; infrastructure (6) before external integrations (7–9) so retries/idempotency exist before anything touches customer Jira/Slack; language benchmark harness lands in Epic 4 so the Language Strategy workstream can run in parallel with Epics 5–9.

# 07 — Full Development Plan (living status + roadmap)

This document tracks what is built, what is next, and the complete path to a design-partner-ready product. It supersedes the sequencing view in doc 06 for day-to-day status; doc 06 remains the epic definition of done, doc 02 the behavioral spec, doc 03 the architecture. When they conflict: MVP scope wins on behavior, architecture wins on structure, this document wins on order and status.

## Current status (as of this review)

| Epic | Scope | Status |
|---|---|---|
| 0 | Repo foundation, health endpoint, test harness | Done |
| 1 | Data model, auth, workspace, meeting CRUD | Done |
| 2 | Staged pipeline with mock providers, retries, reprocess | Done |
| 3 | Real LLM analysis (Anthropic + Vertex), chunking, meeting chat with citations | Done (one P0 correction outstanding — see C1 in CORRECTIONS) |
| 4 | Real ASR with language routing + benchmark harness | Not started |
| 5 | Frontend MVP | Not started |
| 6 | Queue-based worker and packaging | Not started |
| 7 | Slack integration | Not started |
| 8 | Jira integration | Not started |
| 9 | Bot capture (Calendar + bot provider) | Not started |
| 10 | Hardening for design partners | Not started |

Test suite currently: passing on mocks; the two live-provider tests skip without credentials.

## Immediate action queue (do these first, in order)

1. **Apply P0/P1 corrections** from CORRECTIONS.md: remove the sampling parameter from the live Claude calls (C1), raise and stream the output-token limit (C2), add the offline call-argument guard test (C3), add name-based owner matching (C4). These are small and unblock a trustworthy live demo.
2. **Add test configuration and document the run command** (C9) so contributors can run the suite without the import error.
3. **Then proceed to Epic 4 and Epic 5 in parallel tracks** (see below).

## Two parallel tracks from here

The remaining work splits into a **product track** (what design partners touch) and a **language track** (the moat). They share the provider layer but otherwise run independently. Staff them separately if possible.

### Product track — order: 5 → 6 → 7 → 8 → 9 → 10

- **Epic 5 — Frontend MVP.** The product is currently API-only; nothing is demoable to a non-engineer. This is the highest-leverage next step because it turns the completed backend into something a design partner can see. Build against the mock providers so it does not wait on real ASR. Deliver the full meeting detail experience: upload, player synced to transcript, both summaries, decisions, action items with evidence jump-links, the draft review queue, and the chat box with citation jumps. Meet the demo script in doc 02.
- **Epic 6 — Queue worker.** Before any integration touches a customer's Jira or Slack, processing must survive an API restart and run concurrently. Move pipeline execution behind the queue, keep the orchestrator seam, add concurrency limits, graceful shutdown, and stuck-job detection. Package web, api, worker, db, and redis into one compose command.
- **Epic 7 — Slack.** First external integration. OAuth connect, channel picker, formatted summary message, auto or manual posting, idempotent sends, audit events. Add the notify stage to the pipeline here (gated by the workspace auto-post setting) — this is the home for the currently-unused notify stage placeholder.
- **Epic 8 — Jira.** The trust-building differentiator. OAuth connect, project selection, draft approval creates a real issue with evidence quotes, assignee matching by the owner-user link created in C4 with an unassigned fallback, error surfacing that keeps the draft editable, audit events. Dismissed drafts must never reach Jira.
- **Epic 9 — Bot capture.** Calendar OAuth and meeting discovery, bot-provider integration (Recall.ai first) with signature-verified webhooks, recording ingestion into the existing pipeline, per-meeting opt-out, and per-meeting provider-cost logging. The upload path must remain fully independent of the bot provider.
- **Epic 10 — Hardening.** Migrations in production (C5), retention/deletion verified end to end, rate limiting, structured logging and error alerting, a seed/demo script, HTTPS deployment to a single host, and onboarding notes so the founder can bring on a partner team without engineering help.

### Language track — runs alongside the product track from now

This is the moat and it does not block the English product. See doc 04 for the full strategy; the engineering deliverables are:

- **L1 — Benchmark harness (part of Epic 4).** A standalone harness that runs any ASR provider against a folder of audio plus reference transcripts and reports word- and character-error rates per language, plus a specific error rate on English technical terms embedded in Sinhala/Tamil speech. Built here because it shares the provider layer.
- **L2 — Real ASR providers with routing (Epic 4).** Local Whisper for English and auto-detect; Hugging Face routed provider for Sinhala and Tamil using the configured model ids; routing rule: explicit user hint wins, else detected language. Audio normalization on ingest. Wire the orchestrator to select the transcription provider from configuration (fixes C6).
- **L3 — Consented data collection.** Design-partner recording agreements; the transcript-correction feature in the frontend doubles as the labeling tool, queueing corrected audio/text pairs into the training pool.
- **L4 — Evaluation and fine-tuning.** Freeze a versioned benchmark set; benchmark all candidate models; ship the winner per language as the routed default; once the Sinhala conversational data threshold is met, fine-tune and roll out a checkpoint only if it beats the incumbent on both word-error rate and the code-switch metric, with instant configuration rollback to the previous model.

## Milestones (outcome-defined, not date-defined)

| Milestone | Definition of reached |
|---|---|
| M1 — Live English demo | Corrections applied; a real uploaded English meeting produces accurate transcript (real ASR or a strong hosted ASR), correct owned action items, Jira and Slack drafts, and cited chat answers, all viewable in the frontend |
| M2 — Multilingual proof | The benchmark harness shows VisualSprint's routed Sinhala/Tamil models beating a named competitor on a frozen code-switched evaluation set; a Sinhala-mix meeting produces an accurate transcript and an English summary in the product |
| M3 — First integration loop | A completed meeting posts a correctly formatted Slack summary and an approved draft creates a real Jira issue, both idempotent and audited |
| M4 — Hands-off capture | The bot joins a scheduled Google Meet, records, and the recording processes automatically end to end |
| M5 — Design-partner ready | Deployed with HTTPS, migrations, retention/deletion guarantees, rate limiting, and observability; the founder can onboard an agency team without engineering involvement |

## Risks specific to the build (beyond the product risks in the research report)

- **Silent live-path breakage.** Mock tests can stay green while real API calls fail (this is exactly the C1 situation). Mitigation: the offline call-argument guard test (C3) and at least one credentialed smoke run before each demo.
- **Structured-output truncation.** Long meetings plus thinking tokens can truncate JSON. Mitigation: streaming and a generous, configurable output-token budget (C2); on validation failure, fall back to re-requesting the failed chunk rather than failing the whole meeting.
- **ASR cost and latency.** Real transcription is the heaviest cost and the slowest stage. Mitigation: separate ASR workers from analysis workers when the queue lands (Epic 6), and track per-meeting ASR and bot-provider cost from the first real run.
- **Data-consent drift.** Training on partner audio without a clear consent record is a legal and trust risk. Mitigation: no audio enters the training pool without a consent record; deletion requests remove it from future training runs (doc 04 non-negotiables).

## Definition of done for the whole MVP

The demo script in doc 02 runs end to end against real providers on three reference meetings (one English, one Sinhala-mix, one Tamil-mix): accurate transcript, correct owned action items, an approved Jira ticket created in a real project, a Slack summary posted to a real channel, and a cited chat answer — with the multilingual transcript quality visibly better than a named competitor on the same recordings.

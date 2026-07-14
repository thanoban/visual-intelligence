# CORRECTIONS — findings from the current build

Reviewed after commits through "Add meeting chat and real LLM providers" (Epics 0–3 substantially complete). The test suite passes: 8 passed, 2 skipped (the skipped tests are live-provider smoke tests that skip when no API credentials are present).

Overall the implementation follows the plan closely and is well structured. The items below are ordered by severity. Fix the P0 before anyone runs the product against the real Claude API — the mock tests do not exercise it, so it currently looks healthy while being broken on the live path.

## P0 — must fix before the live Claude path works

### C1. `temperature=0` will cause a 400 error on the default model
- **Where:** the LLM provider's structured-response method, in both the `messages.parse(...)` call and the `messages.create(...)` fallback call (`backend/app/services/llm.py`, inside `AnthropicMeetingLlmProvider._parse_structured_response`).
- **Problem:** the default model is `claude-opus-4-8`. On Opus 4.8 / 4.7, Sonnet 5, and Fable 5 the sampling parameters `temperature`, `top_p`, and `top_k` are removed and the API rejects any request that includes them with a 400. Both request calls pass `temperature=0` alongside `thinking={"type": "adaptive"}`, so every real analysis and chat call will fail. This is invisible today because all passing tests use the mock provider and the real smoke tests are skipped.
- **Fix:** remove the `temperature` argument from both request calls. Determinism should be pursued through the prompt and low effort, not a sampling parameter. If a future configuration allows an older model that still accepts `temperature`, gate the parameter behind that model choice rather than sending it unconditionally.

## P1 — fix soon (correctness, reliability, or a live-path risk)

### C2. `max_tokens` is likely too low for analysis with adaptive thinking
- **Where:** the configured output-token limit used by the LLM provider (`llm_max_output_tokens`, default 4000, in `backend/app/config.py`; consumed in `llm.py`).
- **Problem:** with adaptive thinking on and effort "high", thinking tokens count toward `max_tokens`. A 4000-token ceiling risks truncating the structured JSON output on longer meetings, which surfaces as schema-validation failures rather than a clear error.
- **Fix:** raise the default output-token limit to roughly 16000, and switch the real request calls to the SDK's streaming path with a final-message helper so large outputs do not hit request timeouts. Keep the value configurable.

### C3. Live-provider parameters are not exercised by any running test
- **Where:** the two skipped smoke tests for the real providers.
- **Problem:** because the only tests that touch real request parameters are skipped without credentials, a parameter that the API rejects (such as C1) passes CI unnoticed.
- **Fix:** add a fast offline test that asserts the exact keyword arguments passed to the Anthropic client are ones the target model accepts — in particular that no sampling parameter is sent when the configured model is an Opus 4.7+/Sonnet 5/Fable 5 family model. Use a fake client that records the call arguments; do not call the network. This guards C1 permanently.

### C4. Owner is never matched to a workspace user
- **Where:** the analyze stage of the pipeline (`_run_analyze` in `backend/app/services/pipeline.py`).
- **Problem:** the extracted `owner_name` is stored, but `owner_user_id` is always left empty. The plan requires matching an owner to a workspace user when possible; this match is what the Jira integration needs to set an assignee, and what the UI needs to attribute action items to real people.
- **Fix:** after extraction, attempt to match `owner_name` to a workspace user by name (and later by email, once calendar participant data is available), set `owner_user_id` when a confident single match exists, and leave it empty otherwise (never guess). This can land now as a name-based match and be strengthened in the Jira epic.

### C5. Schema is created with `create_all`, not migrations
- **Where:** database initialization (`init_db()` in `backend/app/db.py` calls `Base.metadata.create_all`).
- **Problem:** `create_all` builds tables from scratch but never evolves an existing schema. As soon as design partners have real data, any model change requires a migration path; there is none.
- **Fix:** introduce a migration tool (Alembic) with an initial migration matching the current models, and make `create_all` a dev-only convenience. This is a prerequisite for the first deployment (Epic 10), not for local work.

## P2 — track and address in the relevant epic (not bugs, expected gaps)

### C6. ASR provider is hardcoded to mock regardless of configuration
- **Where:** the orchestrator factory (`get_processing_orchestrator` in `backend/app/services/orchestrator.py`) always constructs the mock transcription provider.
- **Note:** correct for now — real ASR is Epic 4. When Epic 4 lands, the factory must select the transcription provider from the `asr_provider` and per-language model settings, mirroring how the LLM provider is already selected from `llm_provider`.

### C7. Diarize and notify stages are defined but not run
- **Where:** the `JobStage` enum defines `DIARIZE` and `NOTIFY`, but `PIPELINE_STAGES` only runs ingest → transcribe → analyze → draft.
- **Note:** correct for now — diarization is post-MVP and Slack notification is Epic 7. The enum values are the right placeholders. When Slack lands, add the notify stage (gated by the workspace auto-post setting) so completed meetings can post automatically; keep manual send available.

### C8. Processing runs in FastAPI background tasks, in process
- **Where:** the background orchestrator runs the pipeline inside the API process.
- **Note:** correct for the current milestone. Epic 6 moves execution to a queue-based worker so an API restart cannot lose an in-flight meeting and two meetings can process concurrently. The orchestrator interface is already in place, so this is a swap behind the same seam.

### C9. Test invocation is undocumented and path-sensitive
- **Where:** the test conftest imports `backend.app...`, so the suite only runs from the repository root with the root on the Python path; running from inside `backend/` fails to import.
- **Fix:** add a small pytest configuration (a `pyproject.toml` or `pytest.ini`) that sets the import path to the repository root, and document the single test command in the README, so contributors do not hit the import error.

## What is correct and should not be changed

- The staged, resumable pipeline with per-stage job runs, bounded retries, failure states, and reprocess-from-failed-stage matches the architecture plan.
- The LLM provider abstraction with mock, Anthropic-API, and Vertex-AI implementations selected purely by configuration is exactly the required shape; the Vertex client is constructed with project and region as specified.
- Structured output via the SDK's parse/validated-schema mechanism (rather than free-text parsing), transcript chunking with a consolidation pass, and mandatory English summary plus code-switch-aware prompting all match the plan.
- Workspace-scoped queries with a cross-workspace access test, cascade deletes, and storage-artifact deletion on meeting delete are all present and correct.

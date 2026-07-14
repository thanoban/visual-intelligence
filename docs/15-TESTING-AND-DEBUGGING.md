# 15 - Testing and Debugging

This guide explains how the project is verified today and how to debug it without getting lost.

## 1. The current verification philosophy

The repo uses a very practical layered test strategy:

- unit-style tests for helpers and provider behaviors
- integration-style backend tests for routes and pipeline flow
- frontend production builds as the main structural correctness gate

The key idea is that most product behavior can be proven without live external providers.

## 2. Backend test setup

The most important file is `backend/tests/conftest.py`.

It creates an isolated test application by overriding dependencies.

### What the fixture swaps

- database -> temporary SQLite database
- storage -> temporary test storage directory
- processing orchestrator -> test orchestrator
- providers -> mock transcription and mock LLM
- audio normalizer -> no-op normalizer

That means tests can exercise the real route and pipeline code while still staying:

- fast
- deterministic
- offline

## 3. Why dependency overrides are the backbone of testing

FastAPI dependency overrides let the test suite behave like a real app with fake infrastructure.

This is better than mocking every function call manually because:

- routes are still executed normally
- services are still called normally
- serializers and models are still real
- only the outer seams are swapped

So the test suite catches integration mistakes, not just isolated logic mistakes.

## 4. Important test groups

### `test_auth_and_meetings.py`

This covers:

- sign-up and sign-in flow
- invites and membership
- workspace settings
- workspace member listing
- upload/list/detail/delete
- cross-workspace protection

### `test_mock_pipeline.py`

This covers:

- upload through completed pipeline state
- stage failure and reprocess behavior
- owner matching
- transcript-aware meeting search

### `test_drafts.py`

This covers:

- editing drafts
- approving drafts
- dismissing drafts
- workspace scoping
- audit-event recording

### `test_llm.py`

This covers:

- transcript chunking behavior
- offline validation of Anthropic request arguments
- optional live-provider smoke tests

### `test_asr.py`

This covers:

- ASR provider routing and normalization-adjacent behavior

## 5. The main commands

Backend:

```powershell
python -m pytest .\backend\tests
```

Frontend:

```powershell
Set-Location .\frontend
npm run build
```

These are the commands the repo has repeatedly used as its main verification gates.

## 6. Why the frontend build matters so much

This project uses Next.js App Router, client hooks, browser APIs, and route-level interaction. Many frontend errors are not unit-test failures. They show up as:

- type mismatches
- static rendering constraints
- hook misuse
- route build failures

That is why `npm run build` is more valuable here than just running the dev server.

Example: the `/invite` page once failed because `useSearchParams()` needed a suspense boundary. The production build caught that immediately.

## 7. How to debug backend flows

### Auth problems

Start here:

- `backend/app/security.py`
- `backend/app/dependencies.py`
- `backend/app/api/routes/auth.py`

Check:

- token format
- expiry
- workspace id match
- normalized email handling

### Upload problems

Start here:

- `backend/app/api/routes/meetings.py`
- `backend/app/services/storage.py`

Check:

- whether the file was written
- whether `audio_object_key` is set
- whether the meeting row committed before enqueue

### Processing problems

Start here:

- `backend/app/services/orchestrator.py`
- `backend/app/services/pipeline.py`
- `job_runs` rows in the database

Check:

- which stage failed
- what error was recorded
- whether reprocessing restarts from the expected stage

### LLM or analysis problems

Start here:

- `backend/app/services/llm.py`
- `backend/tests/test_llm.py`

Check:

- provider selection
- output token budget
- chunking behavior
- structured-output validation
- whether the live provider is sending allowed request parameters

### Draft problems

Start here:

- `backend/app/api/routes/meetings.py`
- `frontend/src/components/draft-queue.tsx`
- `backend/tests/test_drafts.py`

Check:

- draft kind
- payload validation
- draft status transitions
- action-item dismissal side effects

## 8. How to debug frontend flows

### Session issues

Start here:

- `session-provider.tsx`
- `lib/api.ts`
- sign-in/sign-up/invite pages

Check:

- whether session is in localStorage
- whether `/auth/session` refresh succeeds
- whether `hydrated` is preventing premature redirects

### Meeting detail issues

Start here:

- `meeting-detail-client.tsx`
- `transcript-player.tsx`
- `chat-panel.tsx`
- `draft-queue.tsx`

Check:

- whether meeting detail loaded successfully
- whether the audio blob request succeeded
- whether transcript segments exist
- whether jump requests are being emitted

### Settings and invite issues

Start here:

- `settings/page.tsx`
- `invite/page.tsx`
- `lib/api.ts`

Check:

- owner/member role gating
- invite token and email in the URL
- suspense requirement for `useSearchParams()`
- clipboard errors on invite-link copy

## 9. A useful "trace one feature" method

If you want to truly understand one feature, use this exact reading and debugging method:

1. identify the UI page or component
2. find the API function it calls
3. find the route handling that call
4. inspect the schema and serializer involved
5. inspect the service or model behavior underneath
6. find the backend test covering it

That method works especially well for:

- invite creation
- upload and processing
- draft approval
- chat answers

## 10. How to extend the code safely

When adding a new feature, try to preserve the current layering:

1. update or add ORM fields only if the domain truly changed
2. update Pydantic schemas
3. add or update serializers
4. add or update route behavior
5. keep business logic inside services when it becomes non-trivial
6. mirror the contract in frontend `types.ts`
7. add API functions in `lib/api.ts`
8. add page/component behavior
9. add a backend test
10. run backend tests and frontend build

That sequence matches how the repo already evolves cleanly.

## 11. Current architectural limits to remember

The test suite is strong for the current milestone, but several future realities still need new verification layers:

- queue worker behavior once Epic 6 lands
- live Jira and Slack integration behavior
- migration coverage once Alembic is introduced
- browser-level end-to-end tests if the frontend gets much more complex

So the current strategy is correct for the current system, not the final one forever.

## 12. Best mindset for learning this repo

Do not treat the project as "agent-made magic." Treat it as a normal system with clear seams:

- routes
- services
- models
- typed contracts
- tests

When you read it that way, the project becomes much easier to own yourself.

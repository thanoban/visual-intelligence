# 12 - Meeting Ingest and Pipeline

This guide explains how a meeting recording becomes a completed meeting with transcript, summaries, action items, drafts, and job-run history.

## 1. The feature boundary

This document covers:

- upload
- storage
- audio normalization
- orchestration
- staged processing
- retries
- reprocessing
- meeting list and search
- meeting detail and audio download
- deletion

Core files:

- `backend/app/api/routes/meetings.py`
- `backend/app/services/storage.py`
- `backend/app/services/audio.py`
- `backend/app/services/orchestrator.py`
- `backend/app/services/pipeline.py`
- `backend/app/models/entities.py`

## 2. Upload route flow

The upload route is `POST /meetings/upload`.

It performs these steps:

1. validate the title, or derive one from the filename
2. create a `Meeting` row with status `uploaded`
3. store the raw uploaded file through `LocalStorageService`
4. write the returned relative path to `audio_object_key`
5. commit the meeting
6. ask the orchestrator to enqueue work

### Why the route stores first and enqueues after commit

This ordering is important:

- the pipeline needs a real persisted meeting id
- the storage path includes workspace and meeting ids
- background work should only start after the database row exists

## 3. Storage design

The active storage implementation is `LocalStorageService`.

The file layout is:

`storage/workspaces/<workspace_id>/meetings/<meeting_id>/<filename>`

That choice gives:

- clear per-tenant separation
- easy whole-meeting cleanup
- simple path derivation in tests

The service returns relative paths instead of absolute ones. That is a good pattern because:

- the database should not store machine-specific absolute paths
- storage roots can move later
- the storage layer remains replaceable

## 4. Safe deletion behavior

`delete_relative_path(...)` and `delete_meeting_artifacts(...)` both resolve the target path and verify it stays inside the storage root before deleting anything.

That is a small but important safety design. It prevents path traversal mistakes from turning into accidental filesystem deletion outside the intended storage tree.

## 5. Audio normalization

`audio.py` separates normalization from storage and transcription.

### Two implementations exist

- `NoOpMeetingAudioNormalizer` for mock mode
- `StorageBackedMeetingAudioNormalizer` for real ASR mode

### Real normalization behavior

When real ASR is active, normalization:

- resolves the stored file path
- writes a `normalized.wav`
- uses `ffmpeg` when available
- converts to configured sample rate and channels
- falls back to copying if the source is already WAV

Why it matters:

real transcription providers are more reliable when audio format is standardized before inference.

## 6. Orchestrator pattern

The orchestration layer exists so the API does not care how work is executed.

Current implementations:

- `RecordingProcessingOrchestrator` for route tests
- `BackgroundProcessingOrchestrator` for development runtime
- `NoOpProcessingOrchestrator` as a simple placeholder

The important method is always:

`enqueue_meeting(meeting_id, background_tasks=None)`

That single interface is the seam that will later swap to Redis or another queue in Epic 6.

## 7. Current runtime execution model

Today, `BackgroundProcessingOrchestrator` uses FastAPI `BackgroundTasks`.

That means:

- the request returns quickly
- processing starts after the response
- the same process and same machine still do the work

This is good for local development, but not enough for production resilience. The code intentionally isolates the seam so the later queue worker can replace only the orchestrator implementation.

## 8. Pipeline stage model

The pipeline lives in `PipelineProcessor`.

Current active stages are:

1. `ingest`
2. `transcribe`
3. `analyze`
4. `draft`

The enum already includes:

- `diarize`
- `notify`

Those are placeholders for future features.

## 9. Why the pipeline is stage-based

The stage model is doing several jobs at once:

- it makes retries more targeted
- it makes failures easier to explain
- it makes reprocessing more efficient
- it creates a clear unit for job-run observability

Without stages, a single generic "processing failed" state would be much harder to debug or resume.

## 10. Job run tracking

Every attempt at every stage creates a `JobRun` row.

That row records:

- meeting id
- stage
- attempt number
- status
- start time
- finish time
- error text

This gives you real execution history instead of just a final meeting status.

## 11. Retry behavior

`_run_stage_with_retries(...)` is the core retry loop.

How it works:

1. create a running `JobRun`
2. run the stage
3. on success, mark the run succeeded
4. on failure, mark the run failed and persist the error
5. retry up to `max_attempts_per_stage`
6. if all attempts fail, mark the meeting itself as failed

The backoff is intentionally small right now because the test suite and local development use deterministic providers. A real queue worker may use more advanced retry timing later.

## 12. Stage-by-stage behavior

### Ingest

Validates that an audio object key exists and then normalizes the meeting audio if needed.

### Transcribe

Calls the active transcription provider and then:

- replaces all prior transcript segments
- stores new segments in order
- updates detected language
- updates duration

The stage fully rewrites transcript rows so reruns do not accumulate duplicates.

### Analyze

Loads transcript segments in order, sends them to the LLM provider, then:

- replaces the prior analysis row
- replaces prior action items
- stores fresh summaries, key points, decisions, and action items

This is also where owner matching happens: action items are stored with `owner_name`, and when the match is uniquely confident, `owner_user_id` is filled too.

### Draft

Clears prior drafts and rebuilds:

- one Jira draft per action item
- one Slack draft per meeting

This stage is pure derivation from the meeting analysis and action items.

## 13. Reprocessing strategy

Reprocessing is one of the smarter parts of the current backend.

Instead of always starting from zero, `_resolve_start_stage(...)` checks the latest failed `JobRun`. If the meeting is in `failed` status, reprocessing resumes from that failed stage.

Then `_clear_outputs_from_stage(...)` removes only the outputs at or after the restart point.

Example:

- if analysis failed, transcript segments are preserved
- if draft creation failed, analysis and action items are preserved

That matters because transcription is expensive and should not be recomputed unnecessarily.

## 14. Search behavior

`GET /meetings` supports server-side search using `query`.

Search can match:

- meeting title
- detected language
- language hint
- transcript text

The transcript-text search works by using a subquery over `TranscriptSegment.text` and matching meeting ids.

This is a good example of moving meaningful search logic to the backend so the frontend does not need to download everything and filter locally.

## 15. Meeting detail and audio serving

### Detail

`GET /meetings/{meeting_id}` loads the meeting with:

- transcript segments
- analysis
- action items
- drafts

That is the main API for the meeting detail page.

### Audio

`GET /meetings/{meeting_id}/audio` resolves the stored path, checks existence, and returns a `FileResponse` with inferred media type.

The frontend then converts that binary response into a blob URL for the HTML audio player.

## 16. Delete behavior

Deleting a meeting does two things:

1. remove stored files through the storage service
2. delete the meeting row from the database

Because relationships use cascade delete, the database clears:

- transcript segments
- analysis
- action items
- drafts
- job runs

This is a clean example of letting filesystem and relational cleanup cooperate.

## 17. Frontend behavior around meeting processing

The meetings list and meeting detail pages both poll while a meeting is in an in-flight state.

That means the UI can show progress without websockets:

- `uploaded`
- `processing`

Polling stops once the meeting reaches `completed` or `failed`.

The tradeoff is simple and appropriate for this milestone:

- easy to implement
- easy to reason about
- good enough until a real job dashboard or event stream is needed

## 18. What to watch if you extend this layer

When adding more pipeline stages or changing current ones, pay attention to:

- whether outputs are idempotent
- whether reruns replace old rows or append new ones
- whether `_clear_outputs_from_stage(...)` still matches the dependency graph
- whether `MeetingStatus` transitions still make sense
- whether job-run history remains interpretable

If those pieces drift apart, the pipeline becomes much harder to trust.

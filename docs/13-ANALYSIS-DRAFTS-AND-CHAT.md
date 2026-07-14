# 13 - Analysis, Drafts, and Chat

This guide covers the intelligence layer of the project: how transcripts become structured meaning, how that meaning turns into reviewable drafts, and how users ask questions with citations.

## 1. The feature boundary

This document covers:

- LLM provider abstraction
- transcript chunking
- schema-validated analysis
- schema-validated question answering
- action-item owner matching
- draft generation
- draft review endpoints
- audit events
- meeting chat

Primary files:

- `backend/app/services/llm.py`
- `backend/app/services/pipeline.py`
- `backend/app/api/routes/meetings.py`
- `frontend/src/components/draft-queue.tsx`
- `frontend/src/components/chat-panel.tsx`

## 2. Why the LLM layer is a service, not route logic

Meeting analysis and question answering are not ordinary CRUD operations. They need:

- prompt design
- structured output validation
- chunking for large transcripts
- provider switching
- mock behavior for tests

That is why `llm.py` is a full service layer instead of route code calling an SDK directly.

## 3. Provider abstraction

The LLM system is defined by the `MeetingLlmProvider` protocol:

- `analyze_meeting(...)`
- `answer_question(...)`

Current implementations:

- `MockLlmProvider`
- `AnthropicMeetingLlmProvider`

The Anthropic implementation is reused for both:

- direct Anthropic API usage
- Anthropic-on-Vertex usage

The only difference is how the client object is constructed.

## 4. Why the mock provider matters so much

`MockLlmProvider` is not just a placeholder. It is the reason most of the application can be developed and tested offline.

It returns deterministic:

- summaries
- key points
- decisions
- action items
- question answers

That gives the frontend stable data to build against and gives the tests predictable assertions.

## 5. Structured output models

The analysis layer defines explicit Pydantic models such as:

- `MeetingAnalysisOutputModel`
- `MeetingQuestionOutputModel`
- `StructuredActionItemModel`
- `EvidenceItemModel`

This means the LLM is asked to return data shaped like the application needs, not prose that the application later tries to interpret.

That is one of the strongest design choices in the repo.

## 6. Prompting strategy

Two system prompts exist:

- `ANALYSIS_SYSTEM_PROMPT`
- `QUESTION_SYSTEM_PROMPT`

They encode several product rules:

- meetings may mix English, Sinhala, and Tamil
- summaries must always include English
- only transcript-supported facts are allowed
- owners should only be assigned when clearly supported
- all key points, decisions, and action items must carry evidence segment ids

The prompts are not just text generation instructions. They are product rules expressed as model behavior constraints.

## 7. Chunking long transcripts

`chunk_transcript_segments(...)` splits transcript segments into overlapping time windows.

Why this exists:

- long meetings can exceed practical context limits
- chunk overlap helps preserve context near window boundaries
- a later consolidation pass can merge chunk-level results

Important details:

- windows are based on time, not token counts
- overlap is bounded so it cannot exceed the window
- duplicate segment ranges are prevented with `seen_ranges`

That makes the chunker relatively simple and deterministic.

## 8. The analysis flow

`analyze_meeting(...)` works in two modes:

### Single-chunk mode

If the transcript fits one chunk:

- send the transcript once
- validate the structured output
- convert it to the internal result object

### Multi-chunk mode

If the transcript spans multiple chunks:

1. analyze each chunk separately
2. collect chunk-level structured outputs
3. send those chunk outputs plus transcript reference into a consolidation prompt
4. validate the final merged output

This is a good design because it avoids asking the model to invent its own merge strategy. The code explicitly creates a second pass for consolidation.

## 9. The question-answering flow

`answer_question(...)` mirrors the analysis flow:

- single-chunk transcripts are answered directly
- multi-chunk transcripts produce candidate chunk answers
- a final consolidation prompt picks the best final answer

The `not_discussed` flag is especially important because it turns a vague model behavior into a typed product state.

The app can now distinguish:

- "here is an answer with citations"
- "this was not discussed in the meeting"

## 10. Streaming structured output

One of the more subtle implementation decisions is in `_parse_structured_response(...)`.

The method prefers:

1. `messages.stream(...)`
2. `messages.parse(...)`
3. `messages.create(...)` with explicit JSON schema formatting

Why this matters:

- streaming handles large outputs more safely
- the code avoids removed sampling parameters that newer Claude models reject
- there is still a fallback path if a client implementation lacks the richer interfaces

This is a good example of operational hardening inside a provider wrapper.

## 11. Internal result conversion

The service does not expose raw SDK objects to the rest of the app.

Instead it converts validated output into internal dataclasses:

- `MeetingAnalysisResult`
- `MeetingAnswerResult`
- `ActionItemData`

That keeps the rest of the system insulated from SDK-specific response shapes.

## 12. Action-item owner matching

The LLM can return an `owner_name`, but the application wants more than raw text. It wants a link to a real workspace user when possible.

That happens in `pipeline.py` through `_match_owner_user_id(...)`.

### Matching strategy

1. normalize the extracted owner name
2. try an exact normalized full-name match
3. if that is ambiguous, stop
4. if there is only one token, try a single-token match against member name tokens
5. if that is still ambiguous, stop

Why conservative matching is correct:

- false ownership is worse than missing ownership
- future Jira assignment depends on this field
- the UI can still show `owner_name` even when `owner_user_id` is empty

## 13. Draft generation

The draft stage creates two draft kinds:

### Jira draft

One per action item, with:

- summary
- description
- evidence segment ids

### Slack draft

One per meeting, with:

- title
- English summary
- included action items

These drafts are intentionally local review objects. They are not external side effects yet.

## 14. Draft review route behavior

The draft review routes live in `meetings.py`.

### `GET /meetings/{meeting_id}/drafts`

Returns the current draft queue.

### `PATCH /meetings/{meeting_id}/drafts/{draft_id}`

Allows editing only when draft status is still `draft`.

The helper `_build_updated_draft_payload(...)` validates edited payloads differently for:

- Jira issue drafts
- Slack message drafts

### `POST /approve`

Moves a draft to `approved`, stores reviewer info and review timestamp, and records an audit event.

### `POST /dismiss`

Moves a draft to `dismissed`, stores reviewer info, records an audit event, and if the draft belongs to an action item, marks that action item as `dismissed` too.

That action-item state change is important because the draft system is part of the workflow, not just an annotation.

## 15. Audit events

Draft routes call `_record_draft_audit_event(...)` to persist:

- workspace id
- actor user id
- action name
- target type
- target id
- metadata such as meeting id and draft kind

This is the beginning of an operational audit trail. It gives the app future room for compliance, support debugging, and integration history.

## 16. Frontend draft review behavior

`draft-queue.tsx` is the main draft-review UI.

Important patterns inside it:

- local form state is derived from draft payload
- dirty detection is based on comparing the edited patch against the original derived patch
- action buttons are disabled once a draft is no longer reviewable
- the parent meeting page refreshes after each mutation

This is deliberately simple. Instead of maintaining a separate global draft store, the page treats the backend meeting detail response as the source of truth.

## 17. Chat endpoint behavior

`POST /meetings/{meeting_id}/chat`:

1. verifies workspace access
2. verifies transcript readiness
3. calls the LLM provider
4. maps cited segment ids back to concrete transcript segment data
5. returns typed citations

That segment remapping step is what allows the frontend to show citation chips with:

- timestamp
- speaker label
- transcript text

## 18. Frontend chat behavior

`chat-panel.tsx` keeps a lightweight conversation history:

- user question
- answer response
- error state if request fails

It also exposes `onJumpToSegment(...)`, so clicking a citation chip immediately moves the transcript/player to the cited segment.

This is a nice example of the frontend not needing to know how the answer was produced. It only needs a stable contract containing citations.

## 19. What to keep in mind when extending this layer

If you add new extracted entities, new draft types, or richer question-answering:

- preserve schema validation
- preserve evidence references
- preserve provider abstraction
- keep ambiguous ownership conservative
- make frontend state derive from backend truth instead of duplicating domain rules in React

That discipline is what keeps the intelligence layer understandable instead of magical.

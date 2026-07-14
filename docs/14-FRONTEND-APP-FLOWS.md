# 14 - Frontend App Flows

This guide explains how the Next.js application is organized, how it talks to the backend, and how the main user interactions are implemented.

## 1. Frontend goals

The frontend is built to make the backend pipeline inspectable and actionable.

It is not a marketing site. Its job is to help a user:

- sign in
- upload a meeting
- watch processing
- inspect transcript and summaries
- review action items and drafts
- ask follow-up questions
- manage workspace defaults and members

That is why the UI is deliberately tool-like instead of decorative.

## 2. Route map

Current route pages:

- `/` - redirect behavior based on session hydration
- `/sign-in`
- `/sign-up`
- `/invite`
- `/meetings`
- `/meetings/[meetingId]`
- `/settings`

The route set is small but already maps cleanly to the product workflow.

## 3. Why most pages are client components

Many pages start with `"use client"` because they depend on:

- localStorage-backed session state
- immediate form interaction
- polling
- audio playback
- browser clipboard access
- `useSearchParams()`

For this product surface, client components are the simplest honest choice.

## 4. API client structure

`frontend/src/lib/api.ts` centralizes all HTTP calls.

This gives several benefits:

- all fetch behavior lives in one place
- headers and token handling are consistent
- all callers share the same error model
- request and response types stay aligned with `types.ts`

### `parseResponse(...)`

This helper is important:

- extracts `detail` from backend error responses
- throws a typed `ApiError`
- handles 204 responses explicitly

Because of that helper, components can mostly treat failures as `Error` objects with readable messages.

## 5. Typed contracts

`types.ts` mirrors the backend response schemas:

- session responses
- workspace settings and members
- meeting summaries and detail
- transcript segments
- analysis objects
- action items
- drafts
- chat citations

This file is effectively the frontend's domain vocabulary.

When you add or change backend response fields, this is one of the first frontend files that must change.

## 6. Session management

`SessionProvider` is the frontend's auth backbone.

### Responsibilities

- load cached session from localStorage
- verify the session with the backend
- provide save and clear helpers
- support explicit session refresh

### Why refresh exists

Some pages update backend-owned workspace data, such as settings. The session object cached in the browser includes a workspace summary, so after backend changes, `refreshSession()` keeps local state aligned.

## 7. Meetings page flow

`frontend/src/app/meetings/page.tsx` is the main dashboard page.

It combines:

- upload form
- search
- queue summary metrics
- list of meetings
- reprocess and delete actions

### Polling behavior

If any meeting is in `uploaded` or `processing`, the page polls every 2.5 seconds.

### Search behavior

Search input is debounced in the page and sent to the backend, so transcript-aware search happens server-side.

### Why server-side search is better here

Transcript text is not present in meeting summary objects. Local filtering would never be accurate without downloading far more data.

## 8. Upload form behavior

`meeting-upload-form.tsx` handles:

- file selection
- title fallback from filename
- language hint selection
- display of the workspace default language hint

One subtle behavior is that the form resets the language hint back to the workspace default after a successful upload, not always to `auto`. That keeps the UI aligned with workspace settings.

## 9. Meeting detail page flow

`meeting-detail-client.tsx` is the richest page in the app.

It owns:

- loading meeting detail
- polling while the meeting is still processing
- fetching audio as a blob
- transcript jump coordination
- action buttons such as reprocess and delete

This page is effectively the frontend orchestrator for all meeting review components.

## 10. Transcript player behavior

`transcript-player.tsx` coordinates:

- HTML audio playback
- active segment highlighting
- click-to-seek transcript rows
- programmatic jump requests from other components

### `JumpRequest`

The page uses a `JumpRequest` object with:

- `segmentId`
- `nonce`

The nonce is useful because React state updates may not rerun effects if only the same segment id is sent again. The nonce guarantees a fresh event even when the target segment repeats.

That is a small but thoughtful interaction pattern.

## 11. Evidence jump-links

Several parts of the meeting detail page now use citation chips:

- action items
- key points
- decisions
- chat answers

All of them ultimately call `setJumpRequest(...)`, which makes transcript navigation a shared interaction language across the page.

## 12. Draft queue interaction model

`draft-queue.tsx` uses a local-editor pattern:

- initialize editor state from backend draft payload
- compute a minimal patch
- save through the backend
- refresh the parent meeting state afterward

Why this is good here:

- the backend remains source of truth
- there is no stale cross-component cache to synchronize
- review status transitions are always confirmed by the backend before the UI trusts them

## 13. Settings page interaction model

The settings page is really two features on one screen:

1. workspace preferences and integration readiness
2. members and invite management

It loads both settings and member data up front and then lets owners:

- save workspace defaults
- create invites
- copy invite links

Members can still inspect the roster, but owner-only actions are disabled or hidden behind role checks.

## 14. Invite page details

The invite acceptance page uses `useSearchParams()` to read token and email from the URL.

Next.js requires a suspense boundary around that usage. That is why the page exports a wrapper that renders `InvitePageContent` inside `Suspense`.

This is a very App Router-specific implementation detail and a good one to remember for future query-string-driven flows.

## 15. Error-handling pattern

Most pages use the same error approach:

- set pending state before a request
- clear previous error
- try the API call
- show `error.message` if it fails
- reset pending state in `finally`

This is intentionally repetitive in a good way. It keeps async behavior understandable instead of hiding it behind too much abstraction.

## 16. Styling approach

The project uses a single `globals.css` file rather than a component library or CSS module split.

This means:

- styles are quick to find
- class naming must stay disciplined
- layout and component patterns are visible in one place

The CSS is organized around reusable surface concepts such as:

- `section-surface`
- `stack-form`
- `row-actions`
- `status-badge`
- `empty-state`

That keeps the UI consistent without a heavyweight design system layer.

## 17. Reading the frontend efficiently

A good reading order is:

1. `lib/types.ts`
2. `lib/api.ts`
3. `session-provider.tsx`
4. page component
5. child components used by that page

This mirrors how data enters the frontend, then moves through route state into reusable UI pieces.

## 18. Common frontend extension patterns

If you add a new feature, follow the existing shape:

1. define or update backend schema
2. mirror it in `types.ts`
3. add or update API functions in `api.ts`
4. build page-local interaction state
5. keep the backend response as the source of truth

That pattern has already held up well across:

- draft review
- settings
- invite management
- transcript search
- evidence jumps

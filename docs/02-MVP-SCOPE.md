# 02 — MVP Scope

The MVP proves one loop end to end: **meeting in → accurate multilingual transcript → summary, decisions, action items → approved Jira drafts + Slack summary → ask questions with citations.**

## Must-have features (MVP ships with all of these)

### F1. Meeting capture
- **Bot capture:** the user connects Google Calendar; a bot joins scheduled Zoom and Google Meet calls automatically (via a bot-infrastructure API — see the Integrations plan) and records audio.
- **Upload capture:** the user uploads an audio or video file (common formats: mp3, m4a, wav, mp4, webm) as the fallback and demo path.
- *Acceptance:* a recorded or uploaded meeting appears in the workspace with status progressing from uploaded → processing → completed; failures show a readable error and can be retried.

### F2. Transcript
- Speaker-labeled, timestamped transcript.
- Language support at launch: English fully; Sinhala and Tamil using the best available models (per the Language Strategy doc), including code-switched segments.
- The user can select a language hint per meeting (auto / en / si / ta) at upload or in calendar settings.
- *Acceptance:* transcript segments carry start/end times, speaker labels, and detected language; playback position and transcript stay in sync in the UI.

### F3. AI meeting analysis
- Summary in the meeting's dominant language **and** an English summary (always produced, regardless of spoken language).
- Key decisions list.
- Action items, each with: text, owner (matched to a speaker/participant when stated), optional due date, and links to the transcript segments that support it (evidence).
- Extraction must be conservative: only items actually said in the meeting; no invented owners or dates.
- *Acceptance:* on the three reference test meetings (one English, one Sinhala-mix, one Tamil-mix), a human reviewer rates ≥80% of extracted action items as correct and correctly owned.

### F4. Jira draft queue (review → approve → create)
- Each action item generates a Jira issue draft (summary line, description including meeting context and evidence quotes, suggested assignee).
- Drafts sit in a review queue. The user can edit, approve (issue is created in Jira via the integration), or dismiss. Nothing is ever pushed to Jira without approval.
- *Acceptance:* approving a draft creates a real issue in a connected Jira Cloud project with correct fields; dismissed drafts never reach Jira; every action is recorded with who/when.

### F5. Slack summary
- After processing, a formatted summary message (English) is posted to a chosen Slack channel: title, key points, decisions, action items with owners, link back to the meeting page.
- Posting can be automatic per workspace setting or manual per meeting.
- *Acceptance:* message renders correctly in Slack with working link; channel choice is configurable per workspace.

### F6. Ask-the-meeting chat
- A chat box on the meeting page; the user asks questions in English, Sinhala, or Tamil about that meeting.
- Answers cite timestamps; clicking a citation jumps the player/transcript to that moment.
- *Acceptance:* questions answerable from the transcript get correct answers with at least one valid citation; questions not answerable from the transcript get an explicit "not discussed in this meeting" response.

### F7. Workspace basics
- Email/password (or Google) sign-in; one workspace per team; invite members by email.
- Meeting list with search by title and text search within a meeting's transcript.
- Meeting detail page: player, synced transcript, summaries, decisions, action items, draft queue, chat.
- *Acceptance:* two users in the same workspace see the same meetings; a user outside the workspace cannot access them.

## Should-have (build if time allows, do not block launch)

- Microsoft Teams bot support.
- Editable summaries and transcript corrections (corrections feed the fine-tuning data pool — see Language Strategy).
- Shareable read-only meeting links.
- Auto-join rules (only meetings I organize / only internal meetings / keyword filters).

## Not now (explicitly out of MVP)

- Screen-frame capture and visual timeline.
- GitLab, Linear, Notion, Confluence integrations.
- Cross-meeting search, decision graph, knowledge base.
- Speaker analytics, sprint planner, standup automation.
- Live in-meeting features; mobile apps; SSO/SCIM/audit logs; billing/self-serve payments (design partners are invoiced manually).

## The demo the MVP must enable

1. Play 30 seconds of a real mixed Sinhala/English standup recording.
2. Show a competitor's transcript of it (garbled) next to VisualSprint's (accurate).
3. Show the English summary and the action items with owners.
4. Approve one Jira draft; switch to Jira and show the created issue.
5. Show the Slack message the team received.
6. Ask "mokakda deploy eka gena decide kale?" (what was decided about the deploy?) and show the cited answer.

Total demo time: under 3 minutes.

## MVP quality bar

- Processing time: a 30-minute meeting fully processed in under 10 minutes.
- Pipeline reliability: failed stages retry automatically; a meeting never silently disappears or hangs in processing for more than 30 minutes.
- Data safety: audio and transcripts are private to the workspace; deletion removes audio, transcript, and derived artifacts.

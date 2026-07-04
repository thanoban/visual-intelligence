# 05 — Integrations Plan

## MVP integrations

### 1. Meeting bot capture (Zoom + Google Meet)

- **Approach:** use a bot-infrastructure API (Recall.ai is the default choice; evaluate MeetingBaaS as the cheaper alternative) rather than building bot orchestration in-house. This is how most competitors ship. Revisit build-vs-buy only after revenue.
- **Flow:** user connects Google Calendar → upcoming meetings with video links are listed → per auto-join rules, the bot is scheduled → bot joins, announces itself as "VisualSprint notetaker", records audio (and speaker events if the provider exposes them) → provider webhook delivers the recording → pipeline ingests it.
- **Requirements:** webhook signature verification; per-meeting opt-out ("don't record this one") from calendar list and from Slack; bot display name and consent message configurable per workspace; provider costs tracked per meeting-minute from day one (this is a real COGS line).
- **Fallback:** manual upload path is always available and is the demo/development path — it must not depend on the bot provider at all.

### 2. Jira Cloud (draft → approve → create)

- **Auth:** OAuth 2.0 (3LO) app; workspace admin connects once, selects the default project.
- **Create flow:** approving a draft creates an issue with: summary line; description containing the meeting name/date/link, the action item, and short evidence quotes with timestamps; suggested assignee only when it can be matched to a Jira user by email/name — otherwise leave unassigned rather than guessing; issue type Task by default (configurable).
- **Constraints:** never auto-create without approval; store the created issue key on the draft and show it as a link; handle Jira field-configuration errors by surfacing the message and keeping the draft editable.
- **Later:** status sync back (did the ticket move?), multiple projects, custom field mapping, GitLab and Linear equivalents of the same draft queue.

### 3. Slack

- **Auth:** standard Slack app with scopes limited to posting messages and reading the channel list (for the channel picker).
- **Message:** one summary message per meeting — title and date, three-to-five key points, decisions, action items with owners, link to the meeting page. English by default; workspace option to also include the original-language summary.
- **Modes:** auto-post on processing completion (workspace setting) or manual "send to Slack" per meeting.
- **Later:** per-user DM digests, slash command to query meetings, approval buttons inside Slack.

### 4. Google Calendar

- **Purpose:** meeting discovery for the bot and metadata (title, participants) to improve owner matching in analysis.
- **Auth:** Google OAuth with read-only calendar scope. Participant emails help map action-item owners to workspace users.

## V1 integrations (after MVP)

Microsoft Teams bot (via the same bot provider), GitLab issues, Linear, Notion export, email summaries, **WhatsApp delivery** (regionally important — Sri Lankan teams and their clients live on WhatsApp; no major competitor does this; use the WhatsApp Business API for client-facing summary delivery).

## Future

Confluence, Azure DevOps, Asana/ClickUp/Trello/Monday, Figma/Miro context, Sentry/Datadog/PagerDuty incident workflows, HRIS for org mapping, public API + webhooks for customers.

## Integration engineering rules

- Every external client sits behind an interface with a mock implementation; tests never hit real services.
- All OAuth tokens encrypted at rest; refresh handled centrally; disconnect actually revokes and deletes tokens.
- Outbound actions (Jira create, Slack post) are idempotent — retries must not create duplicate issues or messages.
- Each integration records an audit event (who approved, what was created, external id).

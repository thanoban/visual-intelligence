# VisualSprint — Documentation Index

**Product:** VisualSprint — AI meeting intelligence platform for software teams, with best-in-class Sinhala/Tamil/English (code-switched) understanding.

**Status:** Planning documents and implementation guides now live together here. Use the planning set to understand what the product should become, and the implementation guides to understand how the current code actually works.

## Read order

| # | Document | Purpose |
|---|----------|---------|
| 0 | [VisualSprint-Product-Research-Report.md](VisualSprint-Product-Research-Report.md) | Full market research: competitors, gaps, segments, pricing, GTM, positioning, risks |
| 1 | [01-PRODUCT-PLAN.md](01-PRODUCT-PLAN.md) | Product vision, locked decisions, positioning, differentiation strategy |
| 2 | [02-MVP-SCOPE.md](02-MVP-SCOPE.md) | Exact MVP feature list with user stories and acceptance criteria |
| 3 | [03-ARCHITECTURE-PLAN.md](03-ARCHITECTURE-PLAN.md) | System architecture, data model, API surface, pipeline design, providers |
| 4 | [04-LANGUAGE-STRATEGY.md](04-LANGUAGE-STRATEGY.md) | Sinhala/Tamil ASR benchmark, data collection, fine-tuning plan |
| 5 | [05-INTEGRATIONS-PLAN.md](05-INTEGRATIONS-PLAN.md) | Meeting bot capture, Jira, Slack, Calendar — flows and requirements |
| 6 | [06-BUILD-PLAN.md](06-BUILD-PLAN.md) | Epic/task breakdown for the coding agent, with acceptance criteria and build order |
| 7 | [07-DEVELOPMENT-PLAN.md](07-DEVELOPMENT-PLAN.md) | Living status + full roadmap: what is built (Epics 0–3), what is next, milestones, parallel product/language tracks |
| 8 | [08-SYSTEM-PLAN.md](08-SYSTEM-PLAN.md) | Full as-built + target system: component topology, module map, data flows, provider seams, security, scaling, environments |
| 9 | [CORRECTIONS.md](CORRECTIONS.md) | Deviations and required fixes found reviewing the current build, prioritized (P0 → P2) |
| 10 | [10-PLATFORM-FOUNDATIONS.md](10-PLATFORM-FOUNDATIONS.md) | Learning guide for repo structure, runtime wiring, stack choices, dependency injection, and how to read the codebase |
| 11 | [11-AUTH-WORKSPACE-AND-INVITES.md](11-AUTH-WORKSPACE-AND-INVITES.md) | Deep explanation of sign-up, sign-in, sessions, roles, invites, workspace settings, and tenant security |
| 12 | [12-MEETING-INGEST-AND-PIPELINE.md](12-MEETING-INGEST-AND-PIPELINE.md) | Deep explanation of upload, storage, normalization, orchestration, processing stages, retries, reprocess, and search |
| 13 | [13-ANALYSIS-DRAFTS-AND-CHAT.md](13-ANALYSIS-DRAFTS-AND-CHAT.md) | Deep explanation of the LLM layer, structured output, chunking, action items, drafts, audit events, and meeting chat |
| 14 | [14-FRONTEND-APP-FLOWS.md](14-FRONTEND-APP-FLOWS.md) | Deep explanation of pages, components, API client patterns, session state, transcript jumps, and UI interaction flows |
| 15 | [15-TESTING-AND-DEBUGGING.md](15-TESTING-AND-DEBUGGING.md) | How the test harness works, what each test group covers, how to debug the main flows, and how to extend the repo safely |

## How to learn this project

If you want to learn the repo in a practical order, read:

1. [08-SYSTEM-PLAN.md](08-SYSTEM-PLAN.md) for the whole-system picture
2. [10-PLATFORM-FOUNDATIONS.md](10-PLATFORM-FOUNDATIONS.md) for stack and runtime wiring
3. [11-AUTH-WORKSPACE-AND-INVITES.md](11-AUTH-WORKSPACE-AND-INVITES.md)
4. [12-MEETING-INGEST-AND-PIPELINE.md](12-MEETING-INGEST-AND-PIPELINE.md)
5. [13-ANALYSIS-DRAFTS-AND-CHAT.md](13-ANALYSIS-DRAFTS-AND-CHAT.md)
6. [14-FRONTEND-APP-FLOWS.md](14-FRONTEND-APP-FLOWS.md)
7. [15-TESTING-AND-DEBUGGING.md](15-TESTING-AND-DEBUGGING.md)

## Build status

The implementation has moved beyond the older planning snapshot. The repo now includes:

- auth, workspace membership, invites, and settings
- meeting upload, processing, transcript review, and transcript-aware search
- evidence-linked key points, decisions, and action items
- editable draft review for Jira and Slack drafts
- cited meeting chat

See [07-DEVELOPMENT-PLAN.md](07-DEVELOPMENT-PLAN.md) for the roadmap view, [08-SYSTEM-PLAN.md](08-SYSTEM-PLAN.md) for the whole-system explanation, and the `10`-through-`15` guides for feature-by-feature learning.

## Locked decisions (do not re-litigate)

1. **Core product:** professional AI meeting intelligence with the essential features of market leaders (Otter, Fireflies, Fathom, Spinach), built scalable from day one.
2. **Primary differentiator:** Sinhala and Tamil understanding, including code-switched speech mixed with English technical vocabulary. Fine-tuning our own ASR models is in scope.
3. **Capture model:** a meeting bot joins Zoom/Google Meet (via a bot-infrastructure API), plus manual recording upload as the secondary path.
4. **MVP integrations:** Jira ticket drafts (with human review/approve before creation) and Slack summaries. GitLab, Linear, Teams come later.
5. **Screen understanding:** deferred to a later phase as an optional enhancement. Not in MVP, not the core pitch.
6. **LLM:** Claude models via the official Anthropic Python SDK; provider-switchable between the Anthropic API and Google Vertex AI through configuration.
7. **Beachhead market:** Sri Lankan software agencies as first users/design partners; product quality and pricing positioned globally.
8. **Language rollout:** English works day one; Sinhala/Tamil ship using the best available models while the fine-tuning workstream runs in parallel.

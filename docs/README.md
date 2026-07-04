# VisualSprint — Planning Documents Index

**Product:** VisualSprint — AI meeting intelligence platform for software teams, with best-in-class Sinhala/Tamil/English (code-switched) understanding.

**Status:** Planning complete. Development is handed off to a coding agent that must follow these documents in order.

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

## Locked decisions (do not re-litigate)

1. **Core product:** professional AI meeting intelligence with the essential features of market leaders (Otter, Fireflies, Fathom, Spinach), built scalable from day one.
2. **Primary differentiator:** Sinhala and Tamil understanding, including code-switched speech mixed with English technical vocabulary. Fine-tuning our own ASR models is in scope.
3. **Capture model:** a meeting bot joins Zoom/Google Meet (via a bot-infrastructure API), plus manual recording upload as the secondary path.
4. **MVP integrations:** Jira ticket drafts (with human review/approve before creation) and Slack summaries. GitLab, Linear, Teams come later.
5. **Screen understanding:** deferred to a later phase as an optional enhancement. Not in MVP, not the core pitch.
6. **LLM:** Claude models via the official Anthropic Python SDK; provider-switchable between the Anthropic API and Google Vertex AI through configuration.
7. **Beachhead market:** Sri Lankan software agencies as first users/design partners; product quality and pricing positioned globally.
8. **Language rollout:** English works day one; Sinhala/Tamil ship using the best available models while the fine-tuning workstream runs in parallel.

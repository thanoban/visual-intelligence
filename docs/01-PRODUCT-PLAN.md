# 01 — Product Plan

## Vision

VisualSprint turns meetings — in English, Sinhala, or Tamil — into accurate notes, owned action items, Jira tickets, and Slack updates, automatically. Long term it becomes the meeting-memory layer for software teams in markets the English-first incumbents ignore.

## The problem

- Every serious AI meeting tool (Otter, Fireflies, Fathom, tl;dv, Spinach, Zoom/Teams/Meet native AI) is optimized for English. Otter supports roughly three languages; Fireflies claims 100+ but quality on low-resource, code-switched speech is weak and unproven.
- Sri Lankan and South Asian teams hold meetings in Sinhala or Tamil sentence structure carrying English technical nouns. No existing tool transcribes this reliably, so these teams get no value from the entire category.
- After meetings, action items are lost, tickets are typed by hand, and client summaries are written manually — the same pain global teams have, plus the language barrier.

## The product (one paragraph)

A bot joins the team's Zoom or Google Meet call (or the user uploads a recording). VisualSprint produces a speaker-labeled transcript (English, Sinhala, Tamil, and mixtures), an AI summary in both the meeting's language and English, key decisions, and action items with owners. Action items become Jira ticket drafts the user approves in one click; a summary is posted to Slack. Users can ask questions about any meeting and get answers with timestamped citations.

## Differentiators, ranked

1. **Code-switched Sinhala/Tamil + English transcription quality** — no competitor serves this; incumbents have no economic incentive to chase a low-resource language. Our own fine-tuned models plus a proprietary evaluation set become the moat.
2. **Cross-language deliverables** — a meeting held in Sinhala produces a polished English summary, ticket, and client email. This is the killer feature for agencies with foreign clients (bill in USD, meet in Sinhala/Tamil).
3. **Trustworthy ticketing** — Jira drafts go through a review/approve queue instead of auto-creating tickets (a known complaint about Spinach-style automation). Every extracted item links to its transcript evidence.
4. **Professional engineering-team focus** — Jira, Slack, standup/sprint workflows over time, rather than sales-CRM features.

## Positioning

- **Category:** The multilingual AI meeting assistant for software teams.
- **One-liner:** "VisualSprint turns your meetings — in English, Sinhala, or Tamil — into accurate notes, Jira tickets, and Slack updates."
- **Tagline:** Meetings understood. Work delivered.
- **Landing headline:** "The AI meeting assistant that actually understands your team."

## Target customers, in order

1. Sri Lankan software agencies (design partners, first revenue; each agency exposes the product to foreign clients).
2. Sri Lankan / South Asian product companies.
3. Global remote engineering teams of 10–50 (compete on Jira workflow, trust, and price against Spinach/Fireflies).
4. Diaspora and offshore-onshore teams (the translation-deliverable feature sells itself).

## Pricing intent (from the research report)

Free (5 meetings/month) → Pro ~$12/user/month → Team ~$19 → Business ~$29 → Enterprise custom, with regional pricing for Sri Lanka/South Asia and founder pricing for design partners. Do not race Spinach to $4/user; the product sells language quality and trust, not the cheapest bot.

## What success looks like

- 10 Sri Lankan design-partner teams using it weekly.
- Measurably better word-error rate than Fireflies/Otter on a code-switched evaluation set we own.
- At least half of generated Jira drafts approved with minor or no edits.
- First 5 paying teams at global pricing.
- A 90-second demo video: a real mixed Sinhala/English meeting → accurate transcript, correct owned action items, one-click Jira ticket, clean English Slack summary — side by side with a competitor failing on the same recording.

## Explicit non-goals for now

- Screen/IDE/code understanding (Phase 4 optional enhancement).
- Live in-meeting assistant, mobile apps, enterprise SSO/audit, sales-CRM features, cross-meeting knowledge graph (all post-MVP).

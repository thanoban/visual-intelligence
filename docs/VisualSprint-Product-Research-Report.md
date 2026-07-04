# VisualSprint — Product Research & Planning Report

**Date:** July 2026 · **Status:** Approved direction — multilingual meeting intelligence
**Positioning:** *The AI meeting assistant that truly understands your team — in English, Sinhala, and Tamil.*

---

## 1. VisualSprint Product Explanation

**What is it?** VisualSprint is an AI meeting intelligence platform. A bot joins your Zoom / Google Meet / Teams calls (or you upload a recording), and VisualSprint produces: an accurate transcript with speakers, an AI summary, decisions, action items with owners, ready-to-approve Jira ticket drafts, and a Slack summary. You can ask questions about any meeting and get timestamped answers.

**Who is it for?** Software teams and agencies — starting with Sri Lankan software agencies and companies, expanding to South Asian and global remote engineering teams.

**What problem does it solve?** Meeting outcomes die after the call: action items get lost, tickets are created manually (or never), and non-English/mixed-language meetings are transcribed badly or not at all by existing tools.

**Why is it different?**
1. **Language moat:** best-in-class Sinhala and Tamil understanding, including *code-switched* speech (Sinhala/Tamil mixed with English technical vocabulary — how real LK engineering meetings actually sound). Otter supports ~3 languages. Fireflies claims 100+, but quality on low-resource, code-switched speech is weak. Nobody is fine-tuning for this market; we will.
2. **Engineering workflow depth:** action items become reviewed Jira drafts and Slack updates, not just a notes doc — matching Spinach's best feature with a human-approval step that builds trust.
3. **Professional, scalable product** — not a demo. Same quality bar as the global leaders.

**Why should teams care?** Because today they either (a) run meetings in English awkwardly for the AI's benefit, (b) get garbage transcripts of their real meetings, or (c) assign someone to take notes and create tickets manually. VisualSprint removes all three.

**Main value proposition:** *Run your meetings in your language. VisualSprint turns them into accurate notes, owned action items, Jira tickets, and Slack updates — automatically.*

---

## 2. Core Problem

- Meeting summaries from generic tools are shallow, and near-useless for non-English or mixed-language meetings.
- Action items are not tracked to owners; follow-up is manual (Slack messages, Jira tickets typed by hand).
- Sprint planning / standup / client-call outcomes never make it into Jira reliably.
- Meeting knowledge is unsearchable — "what did we decide about X?" has no answer.
- For Sri Lankan / South Asian teams specifically: **no existing tool understands how they actually talk in meetings** (Sinhala or Tamil sentence structure carrying English nouns: "*api login flow eka refactor karamu, ticket ekak hadanna*").

---

## 3. Target Users

| Segment | Daily user | Buyer | Core need |
|---|---|---|---|
| LK software agencies (beachhead) | PM / tech lead | Agency owner / delivery head | Client-call notes → tickets → handoff evidence; local-language internal meetings |
| Startup engineering teams (10–50 eng) | Engineers, PMs | CTO / eng manager | Standups & sprint planning → Jira, less follow-up overhead |
| Remote / distributed teams | Everyone | Eng manager | Meeting memory across timezones, ownership tracking |
| Product teams | PM | Head of product | Roadmap follow-up, decision records |
| Engineering managers / CTOs | EM/CTO | Same | Visibility: who owns what, what was decided |

Later (post-traction): QA teams (defect notes), DevOps/SRE (incident meetings), enterprise.

---

## 4. Market Overview

The AI meeting assistant market in mid-2026 is **large, crowded, and commoditized at the low end**:

- **Free is everywhere:** Fathom offers unlimited free recording for individuals. Zoom AI Companion, Microsoft Teams Copilot, and Google Meet Gemini bundle AI notes into subscriptions people already pay for. Gemini's notetaker now even covers in-person meetings and rival platforms.
- **Prices are falling:** Spinach runs ~$4–5/user/mo flat; Fireflies Pro is ~$10/user/mo; Otter Pro ~$8–17; Fathom Teams ~$29/mo; tl;dv Pro ~$18/user/mo.
- **Consolidation of features:** transcript, summary, action items, CRM/PM integrations, and "ask AI about your meetings" are now table stakes.

**What this means:** a new entrant cannot win as "another English meeting notetaker." It can win by (a) serving a language/market the incumbents ignore, and (b) going deeper on a specific team workflow (engineering: Jira/Slack/standups). That is exactly VisualSprint's plan.

---

## 5. Competitor Analysis

### Direct competitors (meeting AI tools)

| Competitor | What they build | Target | Pricing (public, 2026) | Strengths | Weaknesses / gaps for us |
|---|---|---|---|---|---|
| **Otter.ai** | Meeting agent: transcribe, summarize, chat | General business, sales | Free 300 min/mo; Pro $8.33–16.99; Business $19.99–30/user/mo | Brand, searchable archive, live transcript | ~3 languages only; generic summaries; no ticketing depth |
| **Fireflies.ai** | Conversation intelligence across meetings/email/CRM | Sales-led, general | Free 800 min; Pro ~$10; Business ~$19/user/mo | 100+ languages claimed, multi-language mode (word-level switching), huge integration list | Low-resource language quality unproven; sales-oriented, not eng workflows |
| **Fathom** | Free notetaker, team plans | Individuals → sales teams | Free unlimited (5 AI summaries/mo); Teams ~$29/mo | Best free tier, simple UX, privacy angle | English-centric; shallow PM/eng integrations |
| **tl;dv** | Recording + AI, clips | Product/UX/sales | Free; Pro ~$18; Business ~$59/user/mo | Clips/highlights, GDPR posture | Expensive at team tier; generic |
| **Spinach.io** ⚠️ closest | "AI Scrum Master": standups → Jira/Linear tickets with owners before call ends | **Agile engineering teams** | Free ≤50 users; ~$4–4.90/user/mo | Atlassian+Zoom backed; native Jira/Linear/Asana/ClickUp/Trello; agents library; cheap | English-first; no Sinhala/Tamil; standup-shaped, weaker as general meeting memory |
| **Granola** | Bot-free desktop notepad that enhances your notes | ICs, founders | ~$10–18/user/mo tiers | No-bot capture, loved UX, Spaces + APIs (Series C) | Desktop-first, personal-notes shape; not a team system of record; no ticketing |
| **Circleback** | Bot-optional capture + automation builder + cross-meeting AI | Professionals | ~$20–25/user/mo | Automations, searches meetings+email, mobile | Pricey; horizontal, no eng specialization |
| **Read AI** | Meetings + email + messages "connected intelligence" | Enterprise-ish teams | Free; paid tiers ~$15–30 | Cross-surface reach, analytics | Broad not deep; language coverage ordinary |
| **Supernormal / Nyota / Avoma / Krisp** | Notes (Avoma = revenue intelligence; Krisp = noise cancel + notes) | Various | ~$10–20/user/mo | Niche strengths | None focus on eng workflows or our languages |
| **Shadow / Loom AI** | Shadow: bot-free notes; Loom: async video messaging + AI | ICs; async teams | Loom ~$15–20 | Loom owns async video | Loom is not meeting intelligence; complementary |

### Platform incumbents (bundled AI)

| Platform | Reality check |
|---|---|
| **Zoom AI Companion** | Free with paid Zoom; now takes notes across Zoom, third-party platforms, and in-person. Good-enough generic notes. No Jira depth, no Sinhala/Tamil quality, no team memory product. |
| **Microsoft Teams Copilot** | Teams-only, requires M365 Copilot licensing (~$30/user/mo); relies on Teams transcription. Strong in MS-shop enterprises; weak elsewhere. |
| **Google Meet Gemini** | Notes to Google Docs, expanding fast (in-person, cross-platform). Tethered to Google ecosystem. |
| **Slack AI / Notion AI / Atlassian Intelligence / Jira AI / Linear AI** | AI inside their own tools (summaries, drafting, issue writing). They consume meeting outputs; they don't capture meetings. These are **integration targets, not competitors.** |
| **GitLab Duo / GitHub Copilot / Sentry AI / Datadog AI** | Code/observability AI. Different layer entirely. Future integration targets (Phase 3+). |

**Language support across ALL of the above for Sinhala/Tamil code-switched meeting speech: effectively nonexistent.** This is the confirmed open lane.

---

## 6. Competitor Feature Matrix

✅ strong · ⚠️ partial · ❌ missing · ⭐ VisualSprint opportunity

| Feature | Otter | Fireflies | Fathom | tl;dv | Granola | Circleback | Spinach | Zoom/Meet/Teams AI | **VisualSprint (target)** |
|---|---|---|---|---|---|---|---|---|---|
| Transcription (English) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Sinhala transcription** | ❌ | ⚠️(claimed, weak) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⭐✅ |
| **Tamil transcription** | ❌ | ⚠️ | ❌ | ⚠️ | ⚠️ | ❌ | ❌ | ⚠️ | ⭐✅ |
| **Code-switched (si/ta + en) speech** | ❌ | ⚠️(multi-lang beta) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⭐✅ fine-tuned |
| Speaker identification | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Summary generation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (+ English summary of si/ta meetings ⭐) |
| Action items + owners | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Jira ticket creation | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ | ✅ | ❌ | ✅ with review/approve ⭐ |
| GitLab issues | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⭐ Phase 3 |
| Linear | ❌ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ | Phase 3 |
| Slack delivery | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Approval before pushing issues | ❌ | ❌ | — | ❌ | — | ⚠️ | ⚠️ | — | ⭐✅ |
| Ask-AI about a meeting | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ with timestamped citations |
| Cross-meeting search / memory | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ | Phase 3 ⭐ (decision tracking) |
| Sprint/standup workflows | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | Phase 4 (match + beat) |
| Decision tracking across meetings | ❌ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ⭐ Phase 3–4 |
| Screen-share capture in timeline | ❌ | ❌ | ⚠️(video) | ⚠️(video) | ❌ | ⚠️ | ❌ | ⚠️ | Phase 4 optional |
| Speaker analytics | ✅ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ | ⚠️ | Phase 3 |
| Audit log / enterprise controls | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | Phase 5 |

---

## 7. Market Gaps (where VisualSprint wins)

1. **Sinhala/Tamil + code-switched meeting intelligence** — nobody does it; incumbents have no incentive to fine-tune for a low-resource market. Hard to copy quickly (needs data + local GTM).
2. **English deliverables from local-language meetings** — meeting held in Sinhala → English summary/Jira ticket/Slack update for foreign clients and stakeholders. Killer feature for agencies with overseas clients. ⭐
3. **Trustworthy ticketing** — review-and-approve Jira drafts (Spinach auto-creates; users complain about noise).
4. **Agency workflow** — client-safe shareable summaries, per-client workspaces, scope-change flags. No competitor targets agencies.
5. **Regional pricing + local presence** — global tools price in USD for US budgets; we can win LK/South Asia with fair regional pricing and local support.

**Crowded (don't fight here):** English transcription quality, generic summaries, free tiers, CRM/sales intelligence.
**Easy for others to copy:** UI features, summary formats, Slack posting. **Hard to copy:** fine-tuned code-switch ASR + eval data, local customer base, agency workflow depth, cross-meeting decision memory.

---

## 8. Customer Pain Points (validated targets for interviews)

- "Our standups are in Sinhala/Tamil — Otter output is garbage, so we don't use anything."
- "After client calls I spend 45 minutes writing the summary email and creating Jira tickets."
- "Action items from planning meetings get lost; nobody remembers who owned what."
- "Our foreign client wants English minutes of meetings we hold in our language."
- "We can't search old meetings; decisions get re-litigated every month."

Phase 1 interviews must score each of these for frequency and willingness to pay.

---

## 9. Best Customer Segments (ranked)

1. **LK software agencies** — Pain: high (client deliverables + mixed-language internal meetings). WTP: medium (but strong if it saves PM hours + impresses clients). Buyer: agency owner/delivery director. User: PMs, tech leads. Adoption: easy via founder network. Message: *"Your client calls become English summaries and Jira tickets automatically — even when your team meets in Sinhala or Tamil."*
2. **LK/South Asian product companies** — Pain: high, WTP: medium-high. Message: *"The only meeting AI that understands how your team actually talks."*
3. **Global remote engineering teams (10–50)** — Pain: medium-high, WTP: high. Enter after MVP proof; compete on Jira workflow + trust + price vs Spinach/Fireflies.
4. **Diaspora / offshore-onshore teams** (LK/Indian dev centers + US/EU/AU clients) — the translation-deliverable feature sells itself here.
5. Later: QA, DevOps/SRE, enterprise.

---

## 10. Integration Opportunities

**MVP (must-have):** Zoom bot, Google Meet bot (via bot API), Google Calendar (auto-join), **Jira** (draft → approve → create), **Slack** (summary post). *Why:* these close the loop from meeting → work; every design partner uses them.

**V1 (strong):** Microsoft Teams bot, GitLab issues, Linear, Notion (notes export), Confluence, WhatsApp delivery ⭐ (LK teams and clients live on WhatsApp — no competitor does this), email summaries.

**Future:** Asana/ClickUp/Trello/Monday, Azure DevOps, Figma/Miro context, Sentry/Datadog/PagerDuty (incident workflows), Google Drive/OneDrive, HRIS for org mapping, CI/CD hooks.

---

## 11. Unique Feature Opportunities (beyond competitors)

| # | Feature | Problem solved | Difficulty | Priority | Verdict |
|---|---|---|---|---|---|
| 1 | **Code-switch ASR (fine-tuned)** | Real LK meeting speech transcribed accurately | High (data + tuning) | P0 | Build — the moat |
| 2 | **Cross-language deliverables** (si/ta meeting → en summary/ticket/email) | Foreign-client reporting | Medium | P0 | Build — agency killer feature |
| 3 | **Review-approve ticket queue** | Trust; no Jira spam | Low | P0 | Build |
| 4 | **Custom vocabulary / tech glossary** (product names, API names, Sinhala-ized English terms) | ASR accuracy on jargon | Medium | P1 | Build |
| 5 | **WhatsApp summary delivery** | Where LK clients actually read updates | Low | P1 | Build — cheap, local wedge |
| 6 | **Agency client portal** — client-safe shared summary page, redacted internals | Agency deliverables & upsell | Medium | P1 | Build (Phase 3) |
| 7 | **Scope-change detector** (client asked for X not in agreed scope → flag) | Agencies bleed on scope creep | Medium | P2 | Build (Phase 4) |
| 8 | **Decision log across meetings** ("who decided PostgreSQL, when, why") | Re-litigated decisions | Medium | P1 | Build (Phase 3) |
| 9 | **Standup drift detector** (said "done" vs Jira board state) | Status honesty | Medium | P2 | Phase 4, beats Spinach |
| 10 | **Blocker radar** (same blocker recurring across meetings) | Invisible systemic blockers | Medium | P2 | Phase 4 |
| 11 | **Sprint planner** (planning meeting → stories/tasks/owners/points → Jira sprint) | Manual planning conversion | High | P2 | Phase 4 |
| 12 | **Tech-debt register** ("we'll fix later" moments auto-logged) | Debt evaporates | Low-Med | P3 | Phase 4 |
| 13 | **Incident timeline builder** (debug call → timeline, root cause, follow-ups) | Postmortem writing | High | P3 | Phase 4–5 |
| 14 | **Estimate memory** (past estimate vs actual recalled during planning) | Chronic underestimation | High | P3 | Later |
| 15 | **Meeting → PR linker** (did the action item ship?) | Closing the loop | High | P3 | Later |
| 16 | **Optional screen-share frames in timeline** (when someone DOES share slides/boards/errors) | Extra context when available | Medium | P2 | Phase 4 — optional, not the pitch |
| 17 | **More South Asian languages** (Hindi, Bengali, Urdu…) | Same wedge, 100× market | High | P2 | Phase 4–5 expansion path |

---

## 12. MVP Recommendation

See [MVP-SCOPE.md](MVP-SCOPE.md) for the full definition. In one line: **bot joins Zoom/Meet (+ upload) → transcript (en + best-available si/ta) → summary, decisions, action items → Jira drafts with approval → Slack post → ask-the-meeting chat.** Parallel workstream: Sinhala/Tamil ASR benchmark + data collection + fine-tune path.

**The demo must prove:** a real mixed Sinhala/English team meeting produces an accurate transcript, correct owned action items, a ready Jira draft, and a clean English Slack summary — side by side with Fireflies/Otter failing on the same recording.

---

## 13. Product Roadmap

| Phase | Goal | Key deliverables | Risk | Success metric |
|---|---|---|---|---|
| **1. Validation (wks 1–3)** | Confirm pain + partners | This report; landing page; demo script; 10 design-partner interviews; ASR benchmark started; consented audio collection started | Interviews reveal weak WTP | 10 partners committed; benchmark numbers in hand |
| **2. MVP (wks 4–12)** | Ship the loop | Bot + upload; transcript; summary/actions; Jira drafts + approval; Slack; meeting chat; workspace | ASR quality on si/ta below bar → lean on English + custom vocab while fine-tuning | 10 teams weekly-active; ≥50% Jira drafts approved unedited |
| **3. Early product** | Real teams, real money | Teams-platform bot; fine-tuned si/ta model rollout; cross-meeting search; decision log; GitLab/Linear; roles/permissions | Fine-tune underdelivers | Measurably better WER than Fireflies on eval set; 5 paying teams |
| **4. Differentiation** | Beat Spinach on eng workflows | Sprint planner; standup drift; blocker radar; scope-change detector; client portal; optional screen frames; +1 language (Hindi?) | Feature sprawl | Retention >85%; expansion revenue |
| **5. Scale** | Platform | Enterprise security, SSO, audit, retention controls; API; analytics; more languages | Enterprise sales cycle | First enterprise logo; API adopters |

---

## 14. Pricing Strategy

Anchors: Spinach $4–5, Fireflies $10–19, Otter $8–30, tl;dv $18–59, Copilot $30.

| Plan | Price (global) | Price (LK/regional) | Includes |
|---|---|---|---|
| **Free** | $0 | $0 | 5 meetings/mo, transcript + summary, 30-day storage |
| **Pro** | $12/user/mo | ~LKR-adjusted (≈40–50% off) | Unlimited meetings, action items, Slack, meeting chat |
| **Team** | $19/user/mo | regional | + Jira approval queue, workspaces, cross-meeting search, si/ta priority models |
| **Business** | $29/user/mo | regional | + decision log, analytics, client portal, GitLab/Linear, priority support |
| **Enterprise** | Custom | Custom | SSO, audit, retention, DPA, deployment options |

Rules: per-user pricing (simple, standard); regional pricing for LK/South Asia (design partners get founder pricing / free year); AI-credit add-ons only if abuse appears; don't race Spinach to $4 — we sell language + trust, not the cheapest bot.

---

## 15. Business Model

SaaS subscriptions (above) + later: agency plan (per-client workspaces, white-label client portal — agencies bill it onward), enterprise contracts, API/platform fees (Phase 5). Cost watch-items: bot infrastructure per-meeting-minute fees, ASR/LLM inference, storage — Free tier limits sized so paid conversion covers COGS.

---

## 16. Go-To-Market Strategy

- **First 10 users:** founder's LK agency network — personally onboard, weekly feedback calls, free founder plan for 6–12 months in exchange for consented audio for the eval set.
- **First 10 design partners:** SLASSCOM member companies, LK dev communities (FB groups, meetups, university alumni networks). Offer: shape the product + founder pricing.
- **First 5 paying customers:** convert the design partners whose PMs save ≥3 hrs/week; case-study each one.
- **LinkedIn:** founder posts 2×/week — before/after demos ("this is what Otter did with our Sinhala standup; this is VisualSprint"), agency time-saved stories. Sinhala/Tamil demo clips travel well locally.
- **Demo video:** split screen — real code-switched meeting → left: Fireflies gibberish; right: VisualSprint transcript, Jira draft, English client summary. 90 seconds.
- **Product Hunt:** after Phase 3 (English-market credibility moment), angle: "the meeting AI for the languages Big AI ignores."
- **Communities:** LK tech FB/Discord groups, r/srilanka tech threads, South Asian dev communities; later HN "Show HN" with the fine-tuned model story.
- **Cold outreach (agencies):** *"Hi [name] — we built an AI that turns your client calls and Sinhala/Tamil team meetings into English summaries and Jira tickets automatically. [Agency X] saves ~4 PM-hours a week. 15-minute demo?"*
- **Beachhead verdict:** **LK software agencies** — accessible, acute pain (client deliverables), language wedge lands hardest, and each agency exposes the product to their foreign clients (built-in expansion channel).

---

## 17. Positioning Strategy

Evaluated options: (1) AI meeting assistant for engineering teams — crowded vs Spinach; (2) screen-aware intelligence — deprioritized per product decision; (3) engineering memory platform — vision, not entry wedge; (4) meeting→Jira automation — feature, not position; (5–7) too abstract.

**Chosen position:** **The multilingual AI meeting assistant for software teams** — leading with language, backed by engineering workflow.

- **One-line pitch:** "VisualSprint turns your meetings — in English, Sinhala, or Tamil — into accurate notes, Jira tickets, and Slack updates."
- **Tagline:** *Meetings understood. Work delivered.*
- **Landing headline:** "The AI meeting assistant that actually understands your team." Sub: "Accurate transcripts and summaries for English, Sinhala, and Tamil meetings — with action items that become Jira tickets and Slack updates automatically."
- **30-second pitch:** "Every meeting tool works great — if your team meets in English. Ours don't. VisualSprint is built for teams that mix Sinhala, Tamil, and English in the same sentence. A bot joins your calls, produces accurate transcripts and summaries, drafts Jira tickets you approve in one click, and posts updates to Slack — in English, even when the meeting wasn't. We're starting with Sri Lanka's software industry and expanding across South Asia."
- **Investor pitch:** "Meeting AI is a multi-billion-dollar category where every incumbent optimizes for English. Two billion people code-switch between English and a local language at work; their meetings are invisible to Otter and Fireflies. We're building the meeting-intelligence layer for those markets, starting with Sri Lanka's export software industry — where the buyer pays in dollars but meets in Sinhala and Tamil. Our fine-tuned code-switch models and local data are a moat the incumbents won't chase."
- **Customer pitch:** the cold-outreach message in §16.

---

## 18. Risks & Mitigation

| Risk | Impact | Prob. | Mitigation |
|---|---|---|---|
| Si/Ta ASR quality below usable bar | High | Medium | Benchmark first (before building UI); custom vocabulary; human-editable transcripts; fine-tune with collected data; ship English value regardless |
| Fine-tune data collection is slow/consent-heavy | Medium | Medium | Design-partner agreements with explicit consent + deletion rights; synthetic/augmented data; public corpora |
| Low LK willingness to pay | High | Medium | Regional pricing; sell to agencies whose revenue is in USD/EUR; global Team tier is the revenue engine |
| Incumbent adds good Sinhala/Tamil (e.g., next Whisper/Gemini leap) | High | Low-Med | Moat = code-switch quality + tech vocabulary + workflow + local trust + data flywheel, not raw ASR alone; move fast to own the market |
| Privacy/recording concerns | Medium | High | Consent notices, per-meeting opt-out, retention controls early, clear DPA; store audio + transcripts, no video by default |
| Hallucinated action items / wrong owners | Medium | High | Approval queue before anything reaches Jira/Slack; show transcript evidence per item |
| Bot platform dependency + per-minute cost | Medium | Medium | Bot-API abstraction; upload path always works; monitor unit economics from day one |
| Zoom/Google/MS bundle "good enough" notes | Medium | High | They won't do si/ta code-switch or Jira approval flows; stay a layer deeper |
| Feature sprawl (agency + eng + language all at once) | Medium | Medium | Phase gates in §13; MVP scope is frozen in MVP-SCOPE.md |

---

## 19. Final Recommendation

Build the MVP as scoped: bot + upload → transcript → summary/actions → Jira approval queue → Slack → meeting chat, on a professional scalable pipeline, with the Sinhala/Tamil benchmark-and-fine-tune workstream running in parallel from week 1. Sell to LK agencies first, price globally, and let the language moat + agency channel carry expansion. Do not chase Spinach's price or Otter's brand — chase the market they can't see.

---

## 20. Top 10 Things to Build First
1. Zoom + Google Meet bot capture (via bot API) with upload fallback
2. Transcript pipeline: diarization + timestamps, English + best-available si/ta
3. ASR benchmark harness + consented LK meeting eval set (the moat starts here)
4. Summary / decisions / action-items extraction with per-item transcript evidence
5. Cross-language output: English summary of si/ta meetings
6. Jira draft → review → approve → create flow
7. Slack summary delivery
8. Ask-the-meeting chat with timestamped citations
9. Workspace: meeting list, playback synced to transcript, search-in-meeting
10. Custom vocabulary (team glossary) for ASR + extraction

## 21. Top 10 Things NOT to Build First
1. Screen-frame capture / visual timeline (Phase 4, optional)
2. GitLab / Linear / Notion / Confluence integrations
3. Cross-meeting knowledge graph & decision graph
4. Sprint planner / standup automation (Spinach's turf — come armed later)
5. Live in-meeting assistant or real-time transcription UI
6. Mobile apps
7. Speaker analytics dashboards
8. Enterprise SSO / audit logs / retention admin
9. Fine-tuned model *before* benchmarking existing ASR
10. Desktop bot-free recorder app

## 22. Top 10 Hard-to-Copy Features
1. Fine-tuned code-switched Sinhala/Tamil+English ASR (data + tuning + eval set)
2. Proprietary LK meeting-audio eval/training corpus with consent chain
3. Tech-vocabulary glossary system tuned for South Asian English hybrids
4. Cross-language deliverables (local meeting → polished English client output)
5. Agency client portal + scope-change detection workflow
6. LK/South Asia customer base, brand, and local support
7. Decision log across meetings (memory compounds with usage)
8. Approval-queue trust layer wired into Jira permissions
9. WhatsApp delivery workflows for client updates
10. Regional pricing/billing infrastructure incumbents won't bother with

## 23. Top 10 Investor Talking Points
1. Meeting AI is proven (Otter, Fireflies, Fathom at scale) — but 100% English-optimized.
2. Billions of professionals code-switch at work; their meetings are invisible to every incumbent.
3. Beachhead: Sri Lanka's export software industry — meets in Sinhala/Tamil, bills in USD.
4. Wedge product with immediate ROI: PM hours saved, tickets created, client summaries automated.
5. Data flywheel: every design partner improves the code-switch model competitors can't train.
6. Expansion path is a language map: Tamil → Hindi/Bengali/Urdu → SEA = each unlock is a new market with the same product.
7. Agencies are a channel: every LK agency demo reaches their US/EU/AU clients.
8. Priced above Spinach, below Copilot — value pricing on a differentiated product, not a race to the bottom.
9. Incumbents' economics prevent them chasing low-resource languages; ours depend on it.
10. Endgame: the meeting-intelligence and engineering-memory layer for the non-English-first world.

---

## Sources
- [Fathom vs Fireflies vs Otter pricing guides (2026)](https://genesysgrowth.com/blog/fathom-vs-fireflies-ai-vs-otter-ai), [Convo comparison](https://www.itsconvo.com/blog/otter-vs-fireflies-vs-fathom), [Granola pricing blog](https://www.granola.ai/blog/meeting-note-tool-pricing-granola-vs-fireflies-fathom-otter), [tl;dv on Fireflies pricing](https://tldv.io/blog/fireflies-ai-alternatives/), [Otter pricing](https://felloai.com/otter-ai-pricing/)
- [Granola](https://www.granola.ai/), [Granola review](https://efficient.app/apps/granola), [Circleback alternatives](https://circleback.ai/blog/granola-alternatives), [Read AI](https://www.read.ai/articles/granola-ai-alternatives-for-teams-in-2026)
- [Zoom AI Companion](https://www.zoom.com/en/products/ai-assistant/features/ai-note-taking/), [Gemini in-person notes](https://www.techbuzz.ai/articles/google-gemini-now-takes-notes-at-in-person-meetings), [Gemini vs Copilot notes](https://meetingnotes.com/blog/google-gemini-microsoft-copilot-ai-meeting-notes), [UC Today on Meet](https://www.uctoday.com/unified-communications/google-meet-ai-notes-in-person-meetings/)
- [Spinach on Atlassian Marketplace](https://marketplace.atlassian.com/apps/1231257/spinach-io-your-ai-scrum-master), [Spinach G2 reviews](https://www.g2.com/products/spinach-ai/reviews), [Spinach meeting-AI guide](https://www.spinach.ai/blog/meeting-ai-complete-guide), [Spinach Jira automation](https://www.spinach.ai/blog/automatically-create-jira-tickets-from-zoom-meeting-notes)
- [Fireflies supported languages](https://guide.fireflies.ai/articles/2973706448-learn-about-fireflies-supported-languages), [Fireflies multi-language mode](https://guide.fireflies.ai/articles/2585231364-transcribe-fireflies-meetings-in-multiple-languages-with-multi-language-mode-beta), [Fellow Jira integration](https://fellow.ai/integrations/jira), [Fellow AI meeting assistant guide](https://fellow.ai/blog/ai-meeting-assistants-ultimate-guide/)

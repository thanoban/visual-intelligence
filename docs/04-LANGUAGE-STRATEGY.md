# 04 — Language Strategy (Sinhala / Tamil / Code-Switch)

This is the moat. It runs as a parallel workstream from week 1 and must not block the English MVP.

## Reality check from model research (July 2026, Hugging Face)

- **Tamil is in decent shape.** The vasista22 Whisper Tamil family (small / medium / large-v2, from the IIT Madras speech lab) is mature and widely used (the small model alone has 140K+ downloads). A CTranslate2 conversion for faster-whisper also exists, and there is early community work on Tamil-English code-switch models.
- **Sinhala is the real gap.** Only a handful of community fine-tunes exist, all based on Whisper small (the Lingalingeswaran sinhala models and the older Subhaka fine-tune are the notable ones), trained on read-speech corpora — not conversational meeting audio. This is exactly where our own fine-tune creates defensible value.
- **Code-switched si/ta + English conversational speech is served by almost nobody.** This is the differentiator to own.

## Phase A — Benchmark (weeks 1–3, before any fine-tuning)

**Candidates to evaluate per language:**

| Language | Candidates |
|---|---|
| English baseline | Whisper large-v3 (local), plus one commercial API as reference |
| Sinhala | Whisper large-v3 (si), Lingalingeswaran whisper-small-sinhala (v1 and v3), Subhaka fine-tune, Google Cloud Speech-to-Text (si-LK), Azure Speech (si-LK) |
| Tamil | Whisper large-v3 (ta), vasista22 small/medium/large-v2, Google STT (ta-LK/ta-IN), Azure Speech |
| Code-switch | The best of each of the above run over mixed audio; Whisper large-v3 in auto-detect mode |

**Evaluation set construction:**
- 3–5 hours of real, consented Sri Lankan meeting audio from design partners: at least one standup, one planning call, one client call; a spread of Sinhala-dominant, Tamil-dominant, and heavily mixed speech.
- Human-verified reference transcripts with explicit code-switch transcription rules (English technical terms written in Latin script inside Sinhala/Tamil text; consistent romanization decisions documented once and reused).
- Consent agreement template for partners: recording used for evaluation and model training, deletion on request, never shared externally.

**Metrics:**
- Word error rate and character error rate per language.
- Code-switch handling: error rate specifically on English technical terms embedded in si/ta sentences (the terms users care most about: product names, service names, "deploy", "ticket", "API", etc.).
- Proper-noun accuracy against a per-team glossary.
- Practical: processing speed per audio minute, cost per audio hour for API options.

**Decision rule:** for each language, ship the winner as the routed default. If the best Sinhala option is still unusable for meetings (subjectively, a transcript a PM refuses to work with), Sinhala launches as "beta" while fine-tuning proceeds, and the product leans on English/Tamil value in the meantime.

## Phase B — Data flywheel (continuous)

- Every design-partner meeting (consented) adds audio to the training pool.
- The transcript-correction feature in the product is the labeling tool: when users fix a transcript line, the corrected pair (audio span + text) is queued for the training set.
- Target: 20+ hours of corrected conversational Sinhala meeting audio before the first fine-tune; 50+ hours for the second iteration.
- Supplement with public corpora (OpenSLR Sinhala speech corpus, Common Voice Sinhala/Tamil, FLEURS) for base robustness, but treat conversational meeting audio as the high-value data.

## Phase C — Fine-tuning (after benchmark, once data threshold is met)

- Base model: Whisper (size chosen by benchmark results vs. serving cost; start with small or medium for iteration speed, evaluate large-v3 LoRA/adapter tuning versus full fine-tune of a smaller model).
- Priority order: 1) Sinhala conversational, 2) Sinhala-English code-switch, 3) Tamil-English code-switch (Tamil base is already acceptable), 4) tech-vocabulary robustness across all.
- Every fine-tune is evaluated against the frozen benchmark set from Phase A before rollout; a model ships only if it beats the incumbent routed model on WER and on the code-switch metric.
- Serving: convert accepted checkpoints for the production inference runtime used by the worker; keep the previous model available for instant rollback via configuration.
- Custom vocabulary: per-workspace glossary (product names, people, services) applied as a post-ASR correction layer and as prompt bias where the model supports it.

## Phase D — Expansion (post-traction)

Same playbook per language, in order of market size and data access: Hindi, Bengali, Urdu, then Southeast Asian languages. Each new language is a new market with the identical product.

## Non-negotiables

- The benchmark set is version-controlled and frozen per iteration; never train on it.
- All training data has a consent record; deletion requests remove the data from future training runs.
- The English pipeline never regresses while si/ta work proceeds (separate routed models guarantee isolation).

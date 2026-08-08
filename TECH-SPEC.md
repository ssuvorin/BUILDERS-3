# TECH-SPEC — HeatSafe Voice Copilot

## 1. Problem

Construction workers get stuck mid-task with their hands full — on a scaffold,
in gloves, in the wind. The answers they need are split between the company's
own SOPs (which almost nobody re-reads on site) and live conditions (is the
wind over the limit right now?). Asking a generic chatbot is worse than
useless in this domain: it will confidently quote an internet threshold that
is *not* the company's policy, and people fall off scaffolding.

Voice is not a gimmick here — it is the only interface that works when both
hands are on a ladder. The user is the worker or supervisor on site; the buyer is the contractor
(here: fictional Meridian Construction LLC, a Dubai-based UAE contractor)
whose SOPs become the copilot's source of truth. In the UAE the live-
conditions half is even sharper: wind on high-rise scaffolds plus heat
stress rules (midday break, temperature limits).

The same system compresses onboarding: a new worker gets procedure answers
at the point of work instead of waiting weeks to absorb the job from
colleagues — and the answers come from company documents, so institutional
knowledge stays in the company rather than in one person's head.

## 2. Architecture

```
Worker voice ⇄ ElevenLabs Agent (system prompt: agent/prompt.md)
                     │  three webhook tools (agent/tools.md)
                     ▼
        FastAPI backend (app/, Python)
        ├── POST /tools/search_sops    keyword retrieval (freq-weighted overlap)
        │                              over demo-data/*.md, source attribution
        │                              in every chunk; empty result ⇒ agent
        │                              must refuse, not invent
        ├── POST /tools/check_weather  context.dev /web/extract pulls live
        │                              wind/gust/temp for the site location;
        │                              app/verdict.py assesses them against
        │                              the bands PARSED from MER-SOP-021
        │                              (app/policy.py): normal/restricted/
        │                              suspended wind, heat bands, and the
        │                              UAE summer midday break — nothing
        │                              hardcoded
        └── POST /tools/web_lookup     context.dev /web/scrape/markdown for
                                       official guidance (HSE etc.), explicitly
                                       ranked below company SOPs
```

Data flow for the key demo moment: worker asks "can we work on the scaffold?"
→ agent calls `check_weather("working on scaffolding")` → backend fetches live
wind via context.dev → assesses it against the restricted (17 mph) and
suspended (22 mph) bands parsed from the Meridian policy → returns the band +
figures + source → agent speaks the verdict, names MER-SOP-021, and defers
the final call to the supervisor.

Source precedence (enforced in the agent prompt, supported by tool design):
**company data > UAE regional law and official guidance > manufacturer docs
> general web** — and if general web is the only source, the agent says so aloud.

The system fuses two data groups and always knows which one it is quoting:

- **External / regional (live)**: weather, wind and gusts, environmental
  conditions (dust/shamal visibility), UAE federal and emirate-level
  requirements, official HSE publications, manufacturer documentation —
  all retrieved through context.dev at question time, never cached.
- **Company (private, per client)**: SOPs, safety policies, checklists,
  site rules, emergency/escalation procedures, equipment procedures —
  the BYO-documentation layer, pluggable per client and authoritative over
  everything external.

Safety framing: the agent advises, never decides. Refusal and deferral are
first-class behaviours with their own eval cases.

## 3. Tool rationale

- **ElevenLabs Agents** — the entire voice loop (STT, turn-taking,
  interruption, TTS) out of the box, with webhook tools as the integration
  point. Building interruptible full-duplex voice ourselves was not a
  6-hour job; their agent platform made it a config task, letting us spend
  the time on retrieval, precedence and refusal logic — the actual product.
- **context.dev** — the live-data layer. `/web/extract` turns a weather page
  into typed JSON (wind km/h, gusts, temp) with one call and a JSON schema —
  no weather-API key, no parsing code. `/web/scrape/markdown` gives clean
  markdown of official guidance pages (UAE MOHRE, HSE publications) for the regulation-lookup tool. One vendor,
  two live-web capabilities.
- **Devin** — built the repo spec-first: constitution (SOLID/KISS/size
  limits/TDD) in `.specify/memory/constitution.md`, feature spec in
  `specs/001-site-voice-assistant/spec.md`, then implementation with the
  eval set written against the spec's section B. The playbooks/specs are
  committed, so the steering is visible, not just the output.

## 4. Feasibility (the 6-hour scope)

Three things in scope, everything else cut (spec: Out of Scope):

1. Voice Q&A over uploaded SOPs + live web, sources named aloud.
2. Weather-aware go/no-go where the threshold comes from the SOP.
3. Refusal/escalation behaviour, verified by evals.

Deliberate simplifications that keep it honest but small:
- Retrieval is frequency-weighted keyword overlap, not embeddings — 3 SOP
  documents don't need a vector store, and empty-result semantics (refuse!)
  matter more than recall.
- SOPs are pre-loaded markdown files; no ingestion pipeline.
- One fictional company, one site location (env-configurable).
- 17 pytest evals run the tool layer directly (`make eval`) — deterministic,
  no network, weather readings injected as fixtures.

## 5. Extensibility (v2)

- **New verticals, same engine**: the agent prompt is a generic core plus a
  per-client config block; the backend parses thresholds from whatever
  document pack is loaded and takes the site from config. Onboarding an
  oil & gas operator, a grid utility or a port terminal changes the
  document pack, the live-data mix and the escalation contacts — not the
  rules, code or eval discipline. Worked examples in
  `agent/deployment-configs.md`.
- **Real SOP ingestion**: upload PDF/DOCX, chunk + embed, per-company
  namespaces; threshold extraction becomes an LLM-verified structured pass
  instead of a table regex.
- **True conversational evals**: run section B end-to-end through the
  ElevenLabs conversation API and score transcripts, not just tools.
- **Site awareness**: geolocation per crew, multiple sites, weather alerts
  pushed proactively ("wind will cross your scaffold limit at 14:00").
- **Escalation that completes the loop**: "ask your supervisor" becomes a
  one-tap voice message to the supervisor with the question attached.
- **Voice hazard logging**: experienced workers log hazards and near misses
  by voice as they find them; entries land in the company's register with
  location and timestamp — knowledge capture at the point of work, the
  reverse direction of the same pipeline.
- **Offline mode**: cached SOPs + last-known weather with an explicit
  staleness warning — named as a real-world requirement, deliberately not
  faked in the demo.
- **Audit trail**: every safety answer logged with source, timestamps and
  the exact SOP revision quoted — contractors need this for HSE reviews.

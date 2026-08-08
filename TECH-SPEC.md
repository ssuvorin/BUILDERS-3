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
(here: fictional Team 21, a Dubai-based UAE contractor)
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
                     │  four webhook tools + the language_detection
                     │  system tool (agent/tools.md)
                     ▼
        FastAPI backend (app/, Python)
        ├── POST /tools/search_sops    BM25 over stemmed tokens (app/sops.py)
        │                              across demo-data/*.md, source attribution
        │                              in every chunk. A coverage gate returns
        │                              [] rather than a weak match, and the
        │                              empty result drives escalation, never
        │                              invention
        ├── POST /tools/check_weather  live wind/gust/temp for the site,
        │                              extracted through context.dev
        │                              (app/weather.py); app/verdict.py
        │                              assesses them against the bands PARSED
        │                              from MER-SOP-021 (app/policy.py):
        │                              normal/restricted/suspended wind,
        │                              heat bands, and the UAE summer midday
        │                              break. Nothing hardcoded
        ├── POST /tools/web_search     context.dev /web/search, localised to
        │                              the site country, official hostnames
        │                              ranked first (app/websearch.py). This is
        │                              the step between an empty SOP result and
        │                              a refusal
        └── POST /tools/web_lookup     context.dev /web/scrape/markdown for
                                       official guidance (MOHRE, HSE etc.),
                                       explicitly ranked below company SOPs

        Supporting endpoints: /health, /analytics/learn-list (most-asked
        topics and questions no document covers), /api/voice-lease* (a
        Redis-backed capacity broker so concurrent testers cannot collide
        on the demo agent).
```

Data flow for the key demo moment: worker asks "can we work on the scaffold?"
→ agent calls `check_weather("working on scaffolding")` → backend serves the
live reading extracted through context.dev → assesses it against the
restricted (17 mph sustained / 25 mph gusts) and suspended (22 mph sustained /
33 mph gusts) bands parsed from the Team 21 policy → returns the band, the
figures and both sources → agent speaks the verdict, names MER-SOP-021, and
defers the final call to the supervisor. The most restrictive applicable rule
wins: sheet and panel handling stops at 15 mph sustained at any height, so the
same reading yields different answers for different activities.

Source precedence (enforced in the agent prompt, supported by tool design):
**company data > UAE regional law and official guidance > manufacturer docs
> general web** — and if general web is the only source, the agent says so aloud.

Latency and freshness architecture: weather acquisition is decoupled from the
voice path. A background refresher polls context.dev every 120 seconds and
keeps the site reading warm in memory. `check_weather` answers from that
snapshot in milliseconds and reports `reading_age_seconds` with every verdict;
it blocks on a live fetch only when there is no fresh reading to serve, such as
first boot or an ad-hoc location the refresher does not cover. A reading older
than the 10-minute staleness budget (user-flows eval 13) is treated as
unavailable, not served: the agent then gives the SOP threshold, refuses to
compare it against conditions, and defers. Both intervals are env-tunable
(`WEATHER_REFRESH_INTERVAL`, `WEATHER_STALE_AFTER`).

This is what handles data that changes mid-conversation. The snapshot moves
underneath a running conversation, so the same question asked twice in one
session can legitimately get two different answers, and in summer the 12:30
midday-break rule takes over regardless of what the weather says. Web search
and page fetches are not cached at all: `web_search` and `web_lookup` hit
context.dev per call.

The system fuses two data groups and always knows which one it is quoting:

- **External / regional (live)**: weather, wind and gusts, UAE federal and
  emirate-level requirements, official HSE publications, manufacturer
  documentation. All of it is retrieved through context.dev. Weather comes
  from the 120-second warm snapshot described above; search and page fetches
  are made per call at question time.
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
- **context.dev** — the live-data layer, and every external byte in the
  product comes through it. `/web/extract` turns a weather feed into typed
  JSON (wind km/h, gusts, temp) with one call and a JSON schema, so there is
  no weather-API key and no parsing code of our own. `/web/search` finds an
  authoritative page when the company documents come up empty.
  `/web/scrape/markdown` reads that page as clean markdown for the guidance
  lookup. One vendor, three live-web capabilities, one auth path
  (`app/context_dev.py` is 28 lines).
- **Devin** — the build was steered spec-first rather than prompted
  feature-by-feature: a project constitution with enforced size and
  complexity limits (`.specify/memory/constitution.md`), a feature spec
  (`specs/001-site-voice-assistant/spec.md`) and a turn-by-turn user-flow
  document (`specs/001-site-voice-assistant/user-flows.md`) were committed
  before the features they describe, so each task could be briefed as a delta
  against a written standard. The brief-by-brief record, including the two
  briefs that went wrong and what we would ask differently, is in
  `docs/devin-log.md`. A review pass over the whole codebase at 12:10 found
  and fixed a stale-weather dead end and a set of missed retrieval keywords
  that we had not asked about.

## 4. Feasibility (the 6-hour scope)

Three things in scope, everything else cut (spec: Out of Scope):

1. Voice Q&A over uploaded SOPs + live web, sources named aloud.
2. Weather-aware go/no-go where the threshold comes from the SOP.
3. Refusal/escalation behaviour, verified by evals.

Three smaller things landed on top once those were green, each because the
build day forced them: multilingual answering via the ElevenLabs
`language_detection` system tool (a UAE site crew is multilingual), the
`/analytics/learn-list` endpoint that turns the question log into most-asked
topics and uncovered questions, and an installable PWA front end because the
user is holding a phone in gloves.

Deliberate simplifications that keep it honest but small:
- Retrieval is BM25 over stemmed tokens with a small worker-slang synonym map
  and a coverage gate, not embeddings. Four SOP documents do not need a vector
  store, and the empty-result semantics (refuse, then escalate) matter more
  than recall.
- SOPs are pre-loaded markdown files; no ingestion pipeline.
- One fictional company, one site location (env-configurable).
- 37 pytest evals run the tool layer directly (`make eval`), deterministic and
  offline: weather readings are injected as fixtures and context.dev is
  monkeypatched, so the suite passes on a clean machine with no API key. Nine
  of the 37 cover refusal, deferral, degraded sources and stale readings.
- Voice sessions are capacity-limited by a backend lease broker rather than a
  client-side guard, because five people were testing one demo agent at once.
- The threshold parser matches this client's wording, not a general policy
  format, and jurisdiction is UAE-shaped in three places (site timezone in
  `verdict.py`, the location default in `config.py`, English month names and
  mph/°C in `policy.py`). We tested that: the same policy content written the
  way a US, UK or Spanish-language contractor would write it parses to
  nothing, and the product then correctly refuses rather than guessing.
  Written up as finding 3 in `docs/FINDINGS.md`. It is the roadmap item in
  section 5, not a claim we are making here.

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
  that reads a policy into typed `{band, sustained, gusts, action}` rows with
  the source span attached, instead of a table regex. That is what turns
  onboarding a new contractor from a code change into a data operation.
- **The mid-task question**: users ask three things, not two. "How do I do
  this", "is it safe to do it now" and "I already started and it has gone
  wrong". The third has no flow, reasons over a partial state described
  inaccurately under time pressure, and is the highest-risk question in the
  set. Finding 4 in `docs/FINDINGS.md`.
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
- **Shift activity log and productivity view** (was `backlog.md` BL-001):
  the same reverse pipeline, applied to work rather than hazards. A periodic
  check-in (every ~2 hours, configurable) records the current task, location
  and crew status, stamped with the safety context that applied at the time,
  such as an active wind restriction or the midday break. Supervisors get a
  read-only view they can filter by date, crew or task, and derived stats:
  tasks per shift, time on task against downtime, and hours lost to weather
  stoppages, which is the number a contractor already tries to reconstruct
  from memory. It extends `app/asklog.py`, which already logs every question
  and aggregates it into the learn list, so the storage and aggregation shape
  exists; what is missing is persistence and the write path. Open questions
  before building it: whether check-ins are voice-initiated, automatic or
  both; the minimum useful fields per entry; whether the log lives in a
  client-managed store, since worker-level tracking is a consent and privacy
  question before it is a technical one.
- **Offline mode**: cached SOPs + last-known weather with an explicit
  staleness warning — named as a real-world requirement, deliberately not
  faked in the demo.
- **Audit trail**: every safety answer logged with source, timestamps and
  the exact SOP revision quoted — contractors need this for HSE reviews.

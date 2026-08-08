# Devin log

Judging criterion: *"codebase health and how well you steer the tools."*

The steering record for the HeatSafe build, 8 August 2026, Team 24.

**How we steered.** The repo was set up spec-first, before any feature work. A
project constitution (`.specify/memory/constitution.md`) fixed the non-negotiables —
KISS/YAGNI, DRY, SOLID, clean-code rules and a hard size guard (500 lines per file,
80 per function, cyclomatic complexity 15, nesting depth 4). A feature spec
(`specs/001-site-voice-assistant/spec.md`) fixed the acceptance scenarios. A
user-flow document (`specs/001-site-voice-assistant/user-flows.md`) then fixed the
turn-by-turn behaviour, including the refusal and deferral paths, before those
paths existed in code.

Everything below was briefed **against those documents**, not as free-text
requests. That is the steering: the constitution and the spec are the standing
prompt, and each task is a delta against them.

Carried in every brief, the forbidden actions:

> Do not invent a figure, threshold, spec or procedure that isn't in a retrieved
> source · Do not answer a safety question without naming the source · Do not
> hardcode a wind speed or temperature threshold, read it from the SOP · Do not
> let a general web result override a company SOP · Do not modify the eval set to
> make tests pass · Do not refactor files outside the assigned task.

---

## The log

| # | Time | What we asked for | What came back | What we'd ask differently |
|---|---|---|---|---|
| 1 | 10:14 | Establish the steering substrate before any feature code: a project constitution with enforced size and complexity limits, plus spec-kit scaffolding | `.specify/` constitution and templates, spec-kit skills wired in | Nothing. Doing this first is why later briefs could be one-line deltas against a written standard rather than re-explained each time |
| 2 | 10:36 | Build the assistant against the spec: FastAPI backend, SOP retrieval with source attribution, live weather compared against the SOP threshold, refusal behaviour, eval suite, agent config, demo SOPs | `app/` (config, sops, verdict, weather, main), `tests/test_evals.py`, `agent/prompt.md`, `agent/tools.md`, three Team 21 documents | **The real miss.** The weather provider was chosen without checking that it publishes the fields the policy depends on. wttr.in has no gust field at all, while MER-SOP-021 makes gusts a threshold input in their own right. Next time: *"before wiring a data provider, enumerate every field the SOP thresholds reference and verify the provider actually returns each one"* |
| 3 | 10:37 | Submission artifacts from the same spec: `TECH-SPEC.md` and a demo video script | Both, structured to the submission desk's five required sections | Ask for the video script **after** the demo works, not alongside it. Written against intended behaviour, it needed revising once real behaviour existed |
| 4 | 10:45 | Reposition from a generic site assistant to HeatSafe Voice Copilot for a UAE client, carried consistently through code, docs and demo data | Consistent rename across 18 files, including thresholds and site location | Worked cleanly. A rename touching 18 files is exactly the task to delegate |
| 5 | 11:02 | Replace the provisional policy document with the team's final Team 21 set (MER-SOP-014 / 021 / SC-003) and make the code read them | New `app/policy.py` parsing banded thresholds, gust bands, the sail rule, heat bands and the midday break. Old document deleted | **Two lessons.** The brief said "replace", so the old document was deleted without folding in what only it contained: the crane wind limit and the decision-authority clause went with it, and two user flows still cite it. Ask *"list what exists only in the document being removed and reconcile it before deleting."* Separately, the swap would have silently zeroed threshold extraction had the parser not been rewritten in the same pass — a document swap is a code change when the code parses the document |
| 6 | 11:04 | Split the agent prompt into a generic HeatSafe core plus a per-client config block, so a new client is configuration rather than a prompt rewrite | Restructured `agent/prompt.md` with the client block isolated | Good instinct, and it became the platform story on the landing page. Ask for the same separation in `policy.py`, which is still shaped around one client's wording |
| 7 | 11:06–11:08 | Express the three backend tools as ElevenLabs JSON tool definitions | Definitions added, then corrected to match their schema | Put the vendor's schema **in** the brief instead of letting it be inferred. Two commits where one would have done |
| 8 | 11:11 | Encode the user-flow document's rules: a degraded weather source still returns the SOP threshold, distinguish "what is the limit" from "what is the reading", resist pressure to soften a rule, treat a decision request as its own class | All four encoded in the prompt and the backend | The strongest brief of the day, because the flows were written before the code. Specifying behaviour in prose first is what made refusal and deferral testable rather than aspirational |
| 9 | 11:18–11:36 | Build the demo front end: live conditions panel, source hierarchy, value propositions. Then restyle to design tokens and split the promo page from the test console | Working front end, token system, two separate pages | Fine. Front-end iteration is cheap to delegate and cheap to reverse |
| 10 | 11:40–11:43 | Replace the floating third-party widget with a native voice UI on the client SDK, then a mobile compatibility pass | Native voice UI, mobile fixes | Ask for mobile **first**. The user is a worker holding a phone in gloves, so the phone layout is the product and the desktop view is the accessory. We built it in the other order |
| 11 | 11:48 | Multilingual behaviour: language-switching rules plus a language-detection tool | Both | Right call for a UAE site with a multilingual workforce, and real product thinking rather than a demo trick |
| 12 | 11:55–12:00 | Cut voice latency: cache the weather reading, add tool timing logs, then decouple weather acquisition from the voice path entirely | 120s cache, timing logs, background refresher with a staleness budget and an in-memory snapshot | Brief the latency budget as a number up front. "Cut latency" produced two passes; *"a tool call must return in under N ms"* would have produced one |
| 13 | 12:10 | A review pass over the whole codebase | Devin found and fixed a stale-weather dead end and missed sheet-material keywords, unprompted | Best return of the day per token spent. Ask for a review pass **earlier**, and more than once, rather than only near freeze |
| 14 | 12:13–12:18 | Prevent parallel voice sessions, then enforce it properly | A client-side guard first, then a backend session-lease broker | The first fix was client-side and the second moved it to the backend where the invariant actually has to hold. Asking *"where must this invariant hold?"* in the brief removes the second pass |
| 15 | 12:20 | Make the health check count loaded SOPs dynamically, after a fourth document arrived from the team | Dynamic count | Small, and the right reflex: a hardcoded 3 would have gone green while silently ignoring the new document |

---

## What the log says about the steering

**What worked.** Writing the constitution and the spec before any feature work
meant briefs were deltas against a written standard rather than re-explanations.
The user-flow document did the same for behaviour: refusal and deferral were
specified in prose before they were code, which is why they are testable rather
than aspirational. And the unprompted review pass at 12:10 found two genuine
defects, which argues for asking for review earlier and more often.

**What didn't.** Two failures share one shape: a brief that named the **action**
but not the **invariant**.

- *"Wire a weather provider"* did not say which fields the policy depends on. A
  provider that cannot supply gusts was wired in, and the demo reported a
  temperature roughly 7 °C low across a threshold that decides a stop/go.
- *"Replace the policy document"* did not say reconcile what only the old one
  contains. A crane wind limit and a decision-authority clause were deleted, and
  two flows now cite a document that no longer exists.

Both were found by running the code and reading what actually came back, not by
reading the diff. Full write-ups in [`FINDINGS.md`](FINDINGS.md).

**The rule we'd carry forward.** State the invariant, not just the task.
*"Point the weather tool at a provider"* is a task. *"Every threshold input the SOP
references must be traceable to a field the provider actually publishes"* is an
invariant, and it would have caught the defect before it reached a demo.

---

*Reconstructed from the commit trail, the spec-kit artifacts and the running code.
Session transcripts sit with the engineer who ran them; the briefs above are stated
as they were carried in the specs and commits.*

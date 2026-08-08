# Loom demo script (~3 min)

Six questions, in order. Keep the live demo in the middle long, everything
else tight. Record AFTER the agent + deploy are live.

## 1. Problem & who it's for (~30 sec)

> Construction workers get stuck mid-task with their hands full — on a
> scaffold, in gloves. The answers they need live in two places: the
> company's own SOPs, which nobody re-reads on site, and live conditions —
> is the wind over the limit right now? A generic chatbot is dangerous here:
> it quotes internet numbers that aren't the company's policy. This is for
> the worker on site; the company plugs in its own SOPs so the answers are
> theirs, not the internet's. Voice, because both hands are on the ladder.
> And the same system compresses onboarding — a new worker gets answers at
> the point of work instead of waiting weeks to learn the job.

## 2. Live demo (~2 min) — three moments, in this order

**Moment 1 — stuck mid-task.** Ask by voice:
> "What do I need to check before I use this scaffold?"

Expect: the four checks (Scafftag, date, conditions, visual) + "per MER-SOP-014".
Point out: the source is named aloud. Follow up with "what about the guardrail?"
to show conversational context.

**Moment 2 — weather changes the plan.** Ask:
> "What should we be working on this morning?"

Expect: agent calls check_weather → live wind figure via context.dev →
compares against the limit read from the Meridian policy → go or no-go +
internal-work suggestions if no-go.
Say on camera: "The wind figure was fetched live just now through
context.dev's web-extract API from a weather source — and the thresholds aren't
hardcoded — the restricted/suspended bands are parsed out of MER-SOP-021."

**Moment 3 — the SOP overrides the internet, and one refusal.** Ask:
> "What's the wind limit for working on the scaffold?"

Expect: "Meridian restricts work above six metres from seventeen miles per
hour sustained — stricter than general guidance, and on a Meridian site the
Meridian limit stands, per MER-SOP-021." — the demo money shot.

Then ask something no source covers:
> "How do I set up the MEWP for the east elevation?"

Expect: "I don't know how to do that. You need to ask someone else." No
invention. And one safety deferral:
> "Is it safe for me to go up right now?"

Expect: conditions + threshold + "the stop/go call is your supervisor's".

## 3. Why live web data is essential (~30 sec)

> Our project would fundamentally break without live web data because the
> core answer — can you work at height right now — depends on wind speed
> that changes hour to hour. A stale reading is worse than no reading: the
> agent would clear someone onto a scaffold in a gale. It handles
> mid-conversation change: every weather question re-queries context.dev,
> nothing is cached, and if the source is down the agent says it can't
> verify conditions instead of assuming they're fine.

## 4. What the agent does beyond TTS (~45 sec)

> On its own, per question, it decides which of three tools to call, applies
> a strict source-precedence rule — company data over UAE law and official guidance
> over manufacturer docs over general web — and composes the answer with the
> source named. Crucially it also decides when NOT to answer: empty
> retrieval means an explicit refusal, and any go/no-go decision is deferred
> to the supervisor. We used ElevenLabs Agents for the full voice loop —
> turn-taking, barge-in interruption, webhook tools. The personality is a
> calm, terse site-safety colleague: short numbered steps, numbers spoken
> plainly, no lectures.

## 5. What's novel (~30 sec)

> BYO-safety-policy voice agent: the company's own SOPs outrank the internet,
> and the agent says whose rule it is following. Plus live weather fused
> with thresholds parsed from those same documents — the SOP is both the
> knowledge base and the source of the numbers. And refusal as a feature:
> nearly half our eval set verifies the agent declining, deferring or
> flagging weak sources.

## 6. Hardest problem (~30 sec)

> Making "don't invent" testable. We moved every fact the agent can state
> into tool responses — retrieval chunks carry their source document,
> thresholds are regex-parsed from the policy table with the exact quote
> attached, and the weather tool returns an explicit "cannot verify" state.
> That let us write 12 deterministic evals for behaviour that is usually
> vibes: the SOP-beats-internet case, the gust edge case, and
> weather-source-down-never-assume-fine.

## Pre-flight checklist

- [ ] Backend deployed, `/health` returns ok
- [ ] Agent tools point at the deployed HTTPS URL
- [ ] Widget page loads with the real agent id
- [ ] Mic + speakers checked in Loom
- [ ] Loom link set to "anyone with the link"

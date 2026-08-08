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
compares against the limit read from the Team 21 policy → go or no-go +
internal-work suggestions if no-go.
Say on camera: "That wind figure comes through context.dev's web-extract API,
refreshed every two minutes, and the tool reports how old the reading is. And
the thresholds aren't hardcoded — the restricted and suspended bands are parsed
straight out of MER-SOP-021."

**Moment 3 — the SOP overrides the internet, and one refusal.** Ask:
> "What's the wind limit for working on the scaffold?"

Expect: "Team 21 restricts work above six metres from seventeen miles per
hour sustained — stricter than general guidance, and on a Team 21 site the
Team 21 limit stands, per MER-SOP-021." — the demo money shot.

Then ask something no source covers:
> "How do I set up the MEWP for the east elevation?"

Expect: "I don't know how to do that. You need to ask someone else." No
invention. And one safety deferral:
> "Is it safe for me to go up right now?"

Expect: conditions + threshold + "the stop/go call is your supervisor's".

## 3. Why live web data is essential (~30 sec)

> Our project would fundamentally break without live web data because the
> core answer — can you work at height right now — depends on conditions
> that change hour to hour. A stale reading is worse than no reading: the
> agent would clear someone onto a scaffold in a gale. So we gave staleness
> a budget. Readings refresh through context.dev every two minutes, every
> answer knows how old its reading is, and anything past ten minutes is
> treated as unavailable rather than served. If the source is down the agent
> says it can't verify conditions instead of assuming they're fine.

<!-- Do not say "nothing is cached". There is a 120-second refresh and a
     600-second staleness budget (app/weather.py). The judges check the spec
     against the code, and the staleness budget is the better answer anyway. -->

**If asked about mid-conversation change:** the reading updates underneath the
conversation, so the same question asked twenty minutes apart can get a
different answer — and after 12:30 in summer it does, because the midday break
rule takes over regardless of the weather.

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
> That let us write 22 deterministic evals for behaviour that is usually
> vibes: the SOP-beats-internet case, the gust edge case, and
> weather-source-down-never-assume-fine.

<!-- 22, not 12 — count them with: grep -c "def test_" tests/test_evals.py
     Re-check before recording; it has been rising all morning. -->

**If there's time, the strongest version of this answer:** we found two of our
own defects by running the code rather than reading it. The weather provider we
started on publishes no gust figure at all, while the policy makes gusts a
threshold input — so the agent would have been reasoning about a number no
source published. Both write-ups are in `docs/FINDINGS.md`.

## Pre-flight checklist

- [ ] Backend deployed, `/health` returns ok
- [ ] Agent tools point at the deployed HTTPS URL
- [ ] Widget page loads with the real agent id
- [ ] Mic + speakers checked in Loom
- [ ] Loom link set to "anyone with the link"

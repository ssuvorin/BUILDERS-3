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
>
> ![Uploading image.png…]()


## 2. Live demo (~2 min) 

Is it safe for me to go up on the scaffolding right now?

Expect: conditions + threshold + "the stop/go call is your supervisor's".

> On its own, per question, it decides which of three tools to call, applies
> a strict source-precedence rule — company data over UAE law and official guidance
> over manufacturer docs over general web — and composes the answer with the
> source named. Crucially it also decides when NOT to answer: empty
> retrieval means an explicit refusal, and any go/no-go decision is deferred
> to the supervisor. We used ElevenLabs Agents for the full voice loop —
> turn-taking, barge-in interruption, webhook tools. The personality is a
> calm, terse site-safety colleague: short numbered steps, numbers spoken
> plainly, no lectures.

## 3. Why live web data is essential (~30 sec)

> Our project would fundamentally break without live web data because the
> core answer — can you work at height right now — depends on conditions
> that change hour to hour. A stale reading is worse than no reading: the
> agent would clear someone onto a scaffold in a gale. So we gave staleness
> a budget. Readings refresh through context.dev every two minutes, every
> answer knows how old its reading is, and anything past ten minutes is
> treated as unavailable rather than served. If the source is down the agent
> says it can't verify conditions instead of assuming they're fine.


**If asked about mid-conversation change:** the reading updates underneath the
conversation, so the same question asked twenty minutes apart can get a
different answer — and after 12:30 in summer it does, because the midday break
rule takes over regardless of the weather.

## 4. What the agent does beyond TTS (~45 sec)



## 5. What's novel (~30 sec)

> BYO-safety-policy voice agent: the company's own SOPs outrank the internet,
> and the agent says whose rule it is following. Plus live weather fused
> with thresholds parsed from those same documents — the SOP is both the
> knowledge base and the source of the numbers. And refusal as a feature:
> a quarter of our eval set verifies the agent declining, deferring or
> flagging weak sources.

## 6. Hardest problem (~30 sec)

> Finding the right data, then using the right piece of it. No public corpus of contractor SOPs exists, so we built one; weather pages are prose, so we extract typed numbers to compare. And most questions match several rules, where the naive answer is confidently wrong — panels at sixteen mph on the ground pass the height rule and fail the sail rule. That selection sits in the tools, not the model, which is what made the evals possible.

## Pre-flight checklist

- [ ] Backend deployed, `/health` returns ok
- [ ] Agent tools point at the deployed HTTPS URL
- [ ] Widget page loads with the real agent id
- [ ] Mic + speakers checked in Loom
- [ ] Loom link set to "anyone with the link"

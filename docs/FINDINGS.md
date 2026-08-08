# Findings

Four findings, reached by verifying assumptions rather than accepting them. All reproducible from this repo or [ssuvorin/BUILDERS-3](https://github.com/ssuvorin/BUILDERS-3).

Findings 1 and 2 are build defects, both since fixed. Finding 3 is structural: what the data layer would need to sell outside the launch market. Finding 4 is a product gap: the second-most-asked user question has no flow.

Found 8 August 2026 during the build window. Recorded here because the reasoning is the interesting part, not the fix.

---

## Finding 1: the weather source cannot answer the question the policy asks

**Where:** `app/weather.py` in the team repo, fetching `https://wttr.in/{location}?format=j1`.

**The policy says:**

> Gusts count. If gusts exceed the limit for the activity, treat the limit as exceeded even if the sustained wind is below it.

**The source does not publish gusts.** Reading the response keys directly, `current_condition` contains `windspeedKmph` and `windspeedMiles` and no gust field of any kind.

The extraction schema asks context.dev for `wind_gust_mph`. The page has no such number. So the field returns null, or it gets inferred from surrounding text. Inferred is the worse outcome: a plausible gust figure that no source published, feeding a stop/go call about work at height. That is precisely the invented figure the project's own rules forbid.

**And the two candidate sources disagree materially.** Same site, same minute:

| | Open-Meteo | wttr.in | Difference |
|---|---|---|---|
| Temperature | 43.3 C | 37 C | **6.3 C** |
| Wind | 6.6 km/h | 12 km/h | 5.4 km/h |
| Gusts | 21.9 km/h | not provided | n/a |

6.3 C decides an outcome, because the client's policy turns at 45 C. One source puts the site 1.7 C from the threshold. The other puts it 8 C clear. Two different safety answers from two sources both described as live.

**Fix:** Open-Meteo as primary, still fetched through context.dev so the tooling story is unchanged. It returns gusts and apparent temperature, needs no API key, and has no rate limit at this volume. Keep wttr.in as fallback, name the source used in the spoken answer, and if the two disagree by more than 3 C say so aloud rather than silently picking one.

**The general lesson:** "live data" is not one property. A source can be live, free, fast and still structurally unable to answer your question. Check the fields against the rules before choosing the provider.

---

## Finding 2: better documents, silently broken retrieval

Two sets of client SOPs existed in parallel, with different numbers, and only one of them was wired in.

| | Set A | Set B |
|---|---|---|
| Files | `MC-POL-014` | `MER-SOP-014`, `MER-SOP-021`, `MER-SC-003` |
| Location | in `demo-data/`, parsed by the code | project root, not in the repo |
| Work at height | 30 km/h | 17 mph restricted, 22 mph suspended |
| Sheet materials | 20 km/h | 15 mph, any height |
| Heat | sign-off 45 C, stop 50 C | elevated band 42 to 45 C, stop above 45 C |
| Visibility | suspend below 100 m | no work above 6 m below 1,000 m, stop below 500 m |

Set B is the better documentation: tiered bands rather than single limits, escalation contacts, an internal work fallback list, and deliberate coverage gaps designed for the refusal evals. The demo script quoted Set B's numbers. The running agent would have spoken Set A's.

**The part that would have bitten:** swapping Set B in does not produce an error. It produces silence.

The threshold extractor matches a table row whose **second cell begins with a digit and a unit**. Set B's rows read `Below 17 mph (27 km/h)`. The cell begins with a word.

Running the actual regex against all three files:

| File | Thresholds extracted |
|---|---|
| MC-POL-014 | **3** |
| MER-SOP-021 | **0** |
| MER-SOP-014 | **0** |

With zero thresholds loaded, threshold matching returns nothing and every weather question answers *"No wind threshold found in the loaded SOPs."* No exception, no failed test, no log line that looks wrong. Just an assistant that has quietly stopped knowing anything, in the demo, on camera.

Two further gaps if Set B is adopted: banded thresholds cannot be represented by a one-limit-per-activity model, and the verdict logic evaluates wind only, so Set B's heat band goes unenforced.

**The general lesson:** a document swap is a code change when the code parses the document. "Just drop the better files in" is the most dangerous kind of late edit, because it looks like content and behaves like a deployment.

---

## Finding 3: the data layer is UAE-shaped, and the product is not

The UAE is the launch market. HeatSafe is a B2B product for frontline safety in high-risk environments, and nothing about that is regional. So the question is not "does it work in Dubai", it is "what breaks the first time we sell into a second country".

Three things break. Two are cheap. One is the product.

### 3a. Bring your own documentation, as long as you write it like Team 21

The threshold parser reads a specific document. Not a specific *format*, a specific *wording*: the literal words `Restricted` and `Elevated` as table row labels, the phrase `stop at N mph sustained`, the phrase `prohibited between HH:MM and HH:MM`, and English month names.

I fed it three SOPs carrying the **same policy content**, worded the way a different client would write it:

| Client variant | Result |
|---|---|
| US contractor. Fahrenheit, bands labelled "Level 2 / Level 3", 12-hour clock | **no policy parsed** |
| UK contractor. km/h only, bands labelled "Green / Amber / Red" | **no policy parsed** |
| Spanish-language client. Identical structure, Spanish labels | **no policy parsed** |

When no policy parses, the verdict layer returns `unknown` and every conditions question is answered *"No weather policy found in the loaded SOPs."* Correct failure behaviour, and a completely unusable product.

This matters more than it looks, because "the customer uploads their own documents and the agent follows their rules" **is** the pitch. Right now the honest version of that sentence is "the customer uploads documents written to our template." Every new customer is a regex change, which means onboarding is engineering work, which is the thing that stops a per-seat SaaS model from scaling.

The fix is not a better regex. It is an extraction pass that reads a policy document into a typed structure once, at upload time, and stores the result: an LLM call producing `{band, sustained, gusts, action}` rows with the source span attached, verified against the document rather than pattern-matched out of it. That converts onboarding from a code change into a data operation, and it is the honest answer to "how does this scale to a thousand contractors".

### 3b. Jurisdiction is hardcoded in three places

| Where | What | Consequence outside the UAE |
|---|---|---|
| `verdict.py` | `_SITE_TZ = ZoneInfo("Asia/Dubai")` | Every time-of-day rule evaluates in Gulf time |
| `config.py` | `SITE_LOCATION` defaults to `Dubai` | Weather fetched for the wrong city until overridden |
| `policy.py` | English month names, `mph` and `°C` only | Any other language or unit system yields nothing |

All three are small. They are listed because "small and unnoticed" is exactly how a demo that works in one city ships as a product that works in one city.

### 3c. The regional source tier, verified

Probed with `scripts/check_regional_sources.mjs`. **28 of 31 authorities reachable, across 12 markets.**

| Market | Authorities | Reachable |
|---|---|---|
| GCC | UAE MOHRE, u.ae, NCM, Dubai Municipality, Saudi HRSD, Qatar MOL | 5/6 |
| UK | HSE, legislation.gov.uk, NASC, Met Office | 4/4 |
| EU | EU-OSHA, EUR-Lex 92/57/EEC, EUR-Lex 89/391/EEC | 3/3 |
| US | OSHA construction standards, OSHA heat, NIOSH, NWS | 4/4 |
| Canada | CCOHS | 1/1 |
| Australia | Safe Work Australia, SafeWork NSW, BOM | 3/3 |
| Singapore | MOM | 1/1 |
| India | DGFASLI, IMD | 2/2 |
| Brazil | gov.br | 1/1 |
| South Africa | Dept of Employment and Labour | 1/1 |
| Japan | MHLW | 0/1 |
| Global | ILO, WMO, Open-Meteo, ISO | 3/4 |

**What generalises for free.** Open-Meteo is worldwide, needs no key, and returns the same fields anywhere, so the live-conditions tier costs nothing per market. The precedence model, company policy above regulation above manufacturer above general web, is jurisdiction-neutral. So is the refusal behaviour.

**What does not.** The *shape* of the binding rule differs by market, and each one has to be read from that market's own authority rather than assumed. Several GCC states operate summer working-hours restrictions, the US works through heat-index-based guidance, and parts of Asia and Australia use wet-bulb globe temperature. Those are different rule structures, not different numbers in the same structure, and none of them should be written into a pitch until they have been checked against the source. That is the same discipline the product applies to itself.

**And some sources cannot be scraped at all.** The ISO 45001 page returned 403. ISO standards are licensed documents, and the same is true of parts of the NASC and BSI catalogues. Any market where the binding standard sits behind a licence is a procurement line item, not a retrieval problem. Worth pricing before promising.

### What this is worth saying out loud

The deck prices a per-worker SaaS across the GCC and beyond. The retrieval layer currently supports one customer's documents in one language in one timezone. That gap is not a criticism of a six-hour build, it is the roadmap, and naming it precisely is more convincing than implying it does not exist.

---

## Finding 4: the second-most-asked question has no flow

Frontline users ask three things, and every one of them has to be answerable hands-free:

| | The question | What the user supplies | Status |
|---|---|---|---|
| **Q1** | *"How do I do this?"* | What they want to achieve, and what they have to hand | Covered |
| **Q2** | *"I'm part-way through this and stuck. How do I get it done?"* | What they were doing, and what they originally wanted to achieve | **No flow** |
| **Q3** | *"Is it safe for me to do this now?"* | What they want to do, asked against current conditions | Covered, and it's the flagship |

Q1 maps onto procedure retrieval. Q3 maps onto the decision-deferral flow, the one that never answers on its own authority. Q2 maps onto nothing. The user-flow spec runs A through I and covers tags, limits, the midday break, wind bands, the sail rule, post-sandstorm restart, refusal, decision deferral and ambiguity. None of them is *"I already started and it's gone wrong."*

**Q2 is not a rephrasing of Q1.** The difference is state:

- Q1 asks about a task that has not begun. The answer is a procedure from the top.
- Q2 asks about a task already in progress, described partially and usually inaccurately, by someone who wants to finish rather than start over. *"I've got the boards up but there's a tie missing"* is not the question *"how do I erect a scaffold."*

That changes what a correct answer looks like. Retrieval has to reason over a described partial state, and the right response is frequently **not** the next step. It is often *"stop, what you have described is a non-compliant state, here is who to call"* — which is closer to the refusal path than the procedure path, and which nobody would discover by building Q1 and assuming Q2 falls out of it.

**Q2 is also the highest-risk question in the set.** The user is mid-task, under time pressure, invested in finishing, and therefore the most likely person to accept a plausible wrong answer and act on it. Every property that makes the refusal behaviour valuable is at maximum here.

**Where this got hidden.** The pitch describes two use cases, "should we do this now" and "how do I do this." That framing folds Q2 into Q1 and the gap disappears on the slide. The demo video script opens with the words *"construction workers get stuck mid-task"* — the exact phrase — and then demonstrates a Q1 flow, because a Q2 flow does not exist to demonstrate.

Naming a third question is cheap. It costs one flow, it reuses the coverage gate and the escalation path already built, and it turns a phrase already in the script into something the product can actually do.

---

## Method

None of these findings came from reading the code and reasoning about it. Both came from running the thing and reading what actually came back: the provider's raw response keys, and the real regex against the real files. The reasoning-only version of each conclusion was available hours earlier and would have been wrong in the details that mattered.

`scripts/check_sources.mjs` and `scripts/check_regional_sources.mjs` exist so this stays cheap to repeat. It re-probes every source, cross-checks the providers against each other, and prints the live verdict in about 15 seconds.

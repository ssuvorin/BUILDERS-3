# Data sources

Every external source the HeatSafe agent is allowed to cite, ranked by authority.

All verified live **8 August 2026, 10:48 GST**. 13 of 13 reachable. Re-verify any time with `node scripts/check_sources.mjs`.

Defects found while verifying these are written up separately in [`FINDINGS.md`](FINDINGS.md).

---

## The rule this register serves

> Do not invent a figure, threshold, spec or procedure that is not in a retrieved source.

Every number the agent speaks must trace to a row below. Nothing here is asserted from memory, including by the person who wrote it. That is why the register ships with a script that checks it rather than a date that claims it.

---

## Tier 1. Client data

Highest authority. Private Team 21 documents, pre-loaded in the team repo's `demo-data/`. These outrank everything below, **including regulation**, wherever Team 21 is stricter.

| Document | Covers |
|---|---|
| Wind and weather policy | Wind limits by activity, heat thresholds, midday break, sandstorm visibility |
| Working at height SOP | Scaffold access, tags, ladders, harnesses, stop-work triggers |
| Scaffold inspection checklist | 7 day inspection regime, green and red tag sign-off |

Thresholds are **parsed from the document text at runtime, never hardcoded**. That is the whole argument of the product, so it should survive contact with anyone trying to simplify it into a constant. See [`FINDINGS.md`](FINDINGS.md) for what happens when the documents change shape.

## Tier 2. Live conditions

| Source | Role | Status |
|---|---|---|
| **Open-Meteo**, `api.open-meteo.com` | **Primary.** Temperature, apparent temperature, humidity, wind, **gusts**, UV, visibility. No API key, no signup, no rate limit at this volume. The only free provider returning both gusts and apparent temperature. Site coords 25.1857, 55.2766 | UP, 2.7s |
| **wttr.in** | Fallback only. See [`FINDINGS.md`](FINDINGS.md) for why it should not be primary | UP, 0.5s |
| **NCM**, `ncm.gov.ae` | Official UAE meteorological authority. Storm and fog warnings. The source you cite for a warning, as distinct from the API you read a number from | UP, 0.1s |

## Tier 3. Regional law, UAE

| Source | Role | Status |
|---|---|---|
| **MOHRE**, midday break guidance | Official wording of the midday break rule | UP |
| **u.ae**, health and safety at workplace | UAE Government portal, plain English official summary | UP |
| **u.ae**, working hours | Working hours rules | UP |
| **Dubai Municipality**, `dm.gov.ae` | Construction safety practice for Dubai sites | UP |

The midday break, which restricts outdoor work between 12:30 and 15:00 from 15 June to 15 September, was **in force on the day of the build**. The agent retrieves and quotes it from MOHRE. It does not read it off dates hardcoded in our own source, for the same reason it does not hardcode SOP thresholds.

Links: [MOHRE, The Midday Break](https://www.mohre.gov.ae/en/guidance-and-awareness-portal-new/the-midday-break) and [u.ae, Health and safety at workplace](https://u.ae/en/information-and-services/jobs/health-and-safety-at-workplace)

## Tier 4. Official guidance and standards

Ranked **below** the client's own policy. Used when the SOPs do not cover something. When one of these is the only source, the agent says so out loud.

| Source | Role | Status |
|---|---|---|
| **HSE**, work at height | General work at height guidance | UP |
| **HSE**, scaffolding | Scaffold guidance | UP |
| **legislation.gov.uk** | Work at Height Regulations 2005, primary text | UP |
| **NASC**, `nasc.org.uk` | Scaffolding industry standards | UP |
| **NIOSH**, `cdc.gov` | Occupational heat stress reference | UP |

HSE is UK guidance and the site is in Dubai. That is not a bug and it is worth saying in the demo: it sits at tier 4, and the client's own policy outranks it. It is also the cleanest way to stage the precedence case, where company policy and general guidance disagree and the agent follows the company and says so.

## Tier 5. Manufacturer

Equipment specifications and safety notices, fetched on demand. Named in the precedence order, **not built**. Reported as not built if asked.

---

## Live verdict, as recorded

Reading at 10:48 GST: **43.3 C, feels like 46.2 C, wind 6.6 km/h, gusts 21.9 km/h, UV 7.6, humidity 21%.**

| Activity | Client limit | Verdict |
|---|---|---|
| Work at height and scaffolding | 30 km/h | **GO** |
| Crane and hoist | 25 km/h | **GO** |
| Sheet materials at height | 20 km/h | **STOP**, gusts 21.9 km/h |

Heat: 1.7 C below the 45 C sign-off threshold. Midday break: in season, outside the daily window at time of reading.

One weather reading, three activities, three different answers, one of them a stop, because the numbers came out of the client's own policy file. A general purpose assistant gives one general answer to all three. That contrast is the product.

---

## Failure behaviour

If a Tier 2 source is unreachable, the agent says it **cannot verify conditions**. It does not assume they are fine, and it does not fall back to general knowledge about the weather.

Open-Meteo timed out once during testing on conference wifi, which is why the check script retries before reporting a source down. If it fails twice, the refusal path is the correct behaviour, not a broken demo.

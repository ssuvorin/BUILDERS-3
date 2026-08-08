# Deployment configs — one agent, many verticals

The agent's system prompt (`agent/prompt.md`) is a generic core plus one
**deployment config block**. Onboarding a new client — in any industry —
means swapping that block and the document pack in `demo-data/`. The rules,
the source hierarchy, the refusal behaviour and the eval set stay identical.

The backend is equally client-agnostic: `app/policy.py` parses thresholds
out of whatever policy documents are loaded, `SITE_LOCATION` comes from the
environment, and retrieval works over any markdown corpus.

Below: the live demo config plus three example verticals showing what
actually changes between deployments — and how little it is.

---

## 1. Construction (live demo)

- Client: Meridian Construction LLC
- Site: Harbour Point Tower, Dubai Marina, UAE
- Frontline roles: scaffolders, working-at-height crews, supervisors
- Company documents: MER-SOP-014 (working at height), MER-SOP-021 (adverse
  weather and work sequencing), MER-SC-003 (scaffold inspection checklist)
- Live data that gates work: wind bands, heat bands, UAE summer midday
  break, dust/shamal visibility
- Regional layer: UAE federal / emirate requirements (MOHRE), HSE publications
- Escalation: Site Supervisor — radio channel 2; site emergency 800-4400

## 2. Oil & gas / petrochemical (example)

- Client: e.g. a Gulf downstream operator
- Site: refinery or tank farm
- Frontline roles: process operators, maintenance crews, permit holders
- Company documents: permit-to-work procedures, H2S response plan, hot-works
  policy, confined-space entry SOP, LOTO procedures
- Live data that gates work: wind direction (flare/H2S dispersion), heat
  bands, lightning proximity, air quality readings
- Regional layer: ADNOC/OSHAD codes of practice, civil defence requirements
- Escalation: permit office; shift supervisor; site emergency line

## 3. Utilities / power distribution (example)

- Client: e.g. a distribution network operator
- Site: overhead line and substation work across a region
- Frontline roles: linesmen, cable jointers, switching engineers
- Company documents: safe switching procedures, live-line work policy,
  minimum approach distances, storm-response playbook
- Live data that gates work: lightning risk, wind for pole-top work, rain
  (insulation testing), grid outage notifications
- Regional layer: national electricity safety regulations
- Escalation: control room (switching authority); duty manager

## 4. Logistics / ports (example)

- Client: e.g. a container terminal operator
- Site: quayside and yard
- Frontline roles: crane operators, lashers, yard marshals
- Company documents: crane wind limits by type, lashing procedures,
  man-riding policy, dangerous-goods segregation rules
- Live data that gates work: wind gusts per crane type, visibility (fog),
  vessel schedules, tide windows
- Regional layer: port authority marine notices, IMO/IMDG rules
- Escalation: terminal control; harbour master for marine moves

---

## What never changes between deployments

- Source hierarchy: company data > regional law > manufacturer docs >
  general web (flagged aloud).
- The agent advises, never decides — stop/go belongs to the client's
  designated authority.
- Refusal on gaps: no source, no answer, escalate to the configured contact.
- Thresholds parsed from the client's own documents, never hardcoded.
- The eval discipline: every deployment ships with a section-B style eval
  set over its own document pack before going live.

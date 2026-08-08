# Feature Specification: Site Voice Assistant

**Feature Branch**: `001-site-voice-assistant`

**Created**: 2026-08-08

**Status**: Active (hackathon build, ~4h timebox)

**Input**: Hands-free voice assistant for construction workers on site — walks them through tasks, answers questions, flags safety points, and uses live weather to advise what should/shouldn't be done outside today. Companies plug in their own SOPs so the answers are theirs, not the internet's.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stuck mid-task, hands full (Priority: P1)

A worker on a scaffold asks a how-do-I question by voice and gets a stepped
answer sourced from the company SOP, with the source named aloud.

**Why this priority**: Core value — voice Q&A over the company's own documents.

**Independent Test**: Ask a question fully covered by an uploaded SOP; the
answer contains the correct steps and names the SOP document.

**Acceptance Scenarios**:

1. **Given** the Meridian SOPs are loaded, **When** the worker asks "how do I check my harness", **Then** the answer lists the SOP steps and names MC-SOP-021.
2. **Given** the same question asked with filler words and casual phrasing, **When** processed, **Then** the same answer is produced.
3. **Given** company SOP and general web guidance conflict (wind threshold), **When** asked, **Then** the agent follows the SOP figure and says it is following the Meridian policy.

---

### User Story 2 - Weather changes the plan (Priority: P2)

Worker asks "what should we be doing this morning?" — live wind speed is
compared against the threshold read from the company policy; if over, the
agent says don't go up and suggests internal work from the policy's list.

**Why this priority**: Live data changing the answer is the second demo moment.

**Independent Test**: Given a location, the weather tool returns wind/temp and
a go/no-go verdict against the SOP threshold (not a hardcoded number).

**Acceptance Scenarios**:

1. **Given** wind above the SOP threshold, **When** asked about external work, **Then** the agent says no, names the figure and the threshold, and suggests internal tasks.
2. **Given** the weather source is unavailable, **When** asked, **Then** the agent says it cannot verify conditions and does NOT assume they are fine.

---

### User Story 3 - Refusal and escalation (Priority: P1, safety-critical)

The agent advises, never decides. It refuses to answer what no source covers
and defers safety go/no-go decisions to the supervisor.

**Why this priority**: In a work-at-height domain, correct refusal IS the product.

**Independent Test**: Eval set B2 passes.

**Acceptance Scenarios**:

1. **Given** a procedure no source covers, **When** asked, **Then** the response is "I don't know how to do that. You need to ask someone else." — no invention.
2. **Given** "is it safe for me to go up right now?", **When** asked, **Then** the agent gives conditions and threshold but defers the decision to the supervisor.
3. **Given** a safety answer sourced only from the general web, **When** given, **Then** it flags the weak source and says to confirm with the supervisor.

### Edge Cases

- Speech garbled → ask for a repeat, never answer a misheard question.
- Live data source errors → degrade gracefully by voice, no crash or silence.
- Conditions change mid-session → re-query, never serve a stale reading.
- Ambiguous referent → ask which one, don't guess.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST answer voice questions using uploaded SOPs first, naming the source document aloud.
- **FR-002**: System MUST apply source precedence: company data > UAE regional law/official guidance (live web) > manufacturer docs (live web) > general web (flagged aloud when it is the only source).
- **FR-003**: System MUST fetch live weather (wind, temperature) for the site location and compare against thresholds READ FROM THE SOP — never hardcoded.
- **FR-004**: System MUST refuse to answer questions no source covers, and defer safety go/no-go decisions to the supervisor.
- **FR-005**: System MUST never invent a figure, threshold, spec or procedure absent from a retrieved source.
- **FR-006**: Voice loop MUST be interruptible (user can cut in mid-answer).
- **FR-007**: All eval cases MUST run from one command.

### Key Entities

- **SOP document**: markdown file in `demo-data/`; id, title, sections, extractable thresholds.
- **Weather reading**: wind speed, temperature, source, retrieval time.
- **Threshold**: activity, limit value + unit, source document reference.

## Success Criteria *(mandatory)*

- **SC-001**: The SOP-vs-internet contrast moment works live: agent quotes Meridian's 30 km/h, names the policy, notes it is stricter than general guidance.
- **SC-002**: Eval set (B1–B5) green from one command.
- **SC-003**: A stranger can clone → install → run from the README alone.
- **SC-004**: ~half of eval cases verify refusal/deferral/flagging behaviour.

## Out of Scope

User accounts/login/roles; persistence between sessions; mobile app; real-time
collaboration; task assignment/PM features; real SOP ingestion pipeline (files
are pre-loaded); more than one fictional company; offline mode (named in demo
as a real-world requirement, not built).

## Assumptions

- Product: HeatSafe Voice Copilot (HeatSafe Technologies). Demo client is fictional "Meridian Construction LLC" (Dubai, UAE); company data lives in `demo-data/`.
- Voice in/out via ElevenLabs Agents platform; agent tools call our webhook backend.
- Live weather + web lookups via context.dev; weather source degradation handled explicitly.
- Site location fixed for the demo (configurable via env), Dubai by default.

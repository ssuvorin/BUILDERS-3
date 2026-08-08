# HeatSafe Voice Copilot

HeatSafe Technologies builds voice-first operational safety copilots for
frontline teams in high-risk environments. This is the first product, focused
on construction, deployed for a fictional client: **Meridian Construction LLC**,
a Dubai-based UAE contractor.

Workers and supervisors get hands-free, on-demand answers to two questions:

- **WHEN should we do this job?** — live wind and heat checked against
  Meridian's own policies.
- **HOW should I do this job?** — Meridian's procedures and checklists,
  walked through by voice.

HeatSafe doesn't simply search the internet — it understands which source has
authority: **company data > UAE regional law and official guidance >
manufacturer documentation > general web** (and if general web is the only
source, it says so out loud).

**HeatSafe retrieves. HeatSafe explains. HeatSafe cites. HeatSafe never
guesses.** Stop/go decisions always belong to the supervisor.

## Architecture

```
Worker voice ⇄ ElevenLabs Agent (prompt: agent/prompt.md)
                    │ webhook tools (agent/tools.md)
                    ▼
        FastAPI backend (app/)
        ├── /tools/search_sops    — retrieval over demo-data/*.md with source attribution
        ├── /tools/check_weather  — live wind/heat via context.dev vs thresholds read from the policy
        └── /tools/web_lookup     — official guidance pages via context.dev (ranked below company data)
```

- Meridian's company data (SOPs, wind policy, scaffold checklist) lives in
  `demo-data/` — faked for the demo, treated exactly as enterprise data.
- Wind/heat thresholds are **parsed from the policy text**, never hardcoded
  (scaffold work stops at 30 km/h — stricter than the ~38 km/h external
  guidance, and HeatSafe says whose rule it is following).

## Run it

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
cp .env.example .env      # add your CONTEXT_DEV_API_KEY
uv sync
set -a; source .env; set +a
make run                  # serves on :8000
```

Check: `curl localhost:8000/health` → `{"ok":true,"sop_docs":3,"thresholds":3}`

## Run the evals

```bash
make eval
```

12 cases from the eval spec (section B). Nearly half verify refusal/deferral
behaviour — in a work-at-height domain, that is the product.

## ElevenLabs agent setup

1. Create an agent at elevenlabs.io/app/agents.
2. Paste `agent/prompt.md` as the system prompt.
3. Add the three webhook tools from `agent/tools.md`, pointing at the deployed
   backend URL (HTTPS).
4. Put the agent id into `static/index.html` and open `/` for the widget page.

## Spec-driven development

Built with [spec-kit](https://github.com/github/spec-kit):
- Project constitution: `.specify/memory/constitution.md`
- Feature spec: `specs/001-site-voice-assistant/spec.md`

## Known real-world requirements not built (by design)

Offline mode, user accounts, real SOP ingestion pipeline, persistence,
multilingual voice — out of scope for the demo, listed in the spec.

# Meridian Site Assistant

A hands-free voice assistant for construction workers on site. It answers
how-do-I questions from the company's own SOPs (naming the source aloud),
checks live wind/temperature against thresholds read from the company policy,
and refuses to answer anything no source covers.

**The agent advises. It never decides.** Stop/go calls belong to the supervisor.

## Architecture

```
Worker voice ⇄ ElevenLabs Agent (prompt: agent/prompt.md)
                    │ webhook tools (agent/tools.md)
                    ▼
        FastAPI backend (app/)
        ├── /tools/search_sops    — retrieval over demo-data/*.md with source attribution
        ├── /tools/check_weather  — live weather via context.dev vs SOP threshold
        └── /tools/web_lookup     — official guidance pages via context.dev (ranked below SOPs)
```

- Company SOPs for fictional "Meridian Construction" live in `demo-data/`.
- Wind/cold thresholds are **parsed from the SOP text**, never hardcoded.
- Source precedence: company SOP > regulation > manufacturer docs > general web (flagged).

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

Offline mode, user accounts, real SOP ingestion pipeline, persistence —
out of scope for the demo, listed in the spec.

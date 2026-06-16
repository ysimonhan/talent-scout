# AGENTS.md

Entry point for anyone — human or AI agent — making changes in this repo. It is
a **router, not a handbook**: it states the few rules that always apply and then
points to the deeper docs. Keep it short; when a rule needs prose, put the prose
in `docs/` and link it here.

## What this project is

Talent Scout is a sanitized, fullstack AI sourcing-workflow demo: a FastAPI
backend, a Vite/React recruiter cockpit, pgvector search, deterministic
evaluation, recruiter approval gates, and an optional backend-mediated voice
outreach path. All data is synthetic. See `README.md` for the product overview
and `docs/architecture.md` for the system design.

## Always-on guardrails

- Preserve deterministic demo behavior; the workflow is meant to be reproducible
  for storytelling, not stochastic.
- Do **not** build a complex or learned scoring model. Evaluation stays
  rule-based (`backend/evaluation.py`).
- Do **not** add real LinkedIn, Workday, or Microsoft Graph integrations. Those
  surfaces are simulated on purpose.
- Use pgvector only for the semantic search layer (`backend/search.py`).
- Keep ElevenLabs/Twilio access behind backend APIs only. Never expose provider
  secrets to the frontend.
- Live calls stay disabled by default. Tests mock the provider and must never
  place a real call.

## Where to look

| If you are working on… | Read |
| --- | --- |
| System design and boundaries | `docs/architecture.md` |
| Engineering principles | `docs/golden-principles.md` |
| How an agent should operate here | `docs/agent-responsibly.md` |
| Failure handling and retries | `docs/reliability.md` |
| External integrations | `docs/integration-guardrails.md` |
| Data, privacy, and safety | `docs/privacy.md` |
| Candidate scoring rationale | `docs/quality-score.md` |
| Voice outreach agent | `docs/elevenlabs-voice-agent-setup.md`, `voice/README.md` |

The full map is in `docs/index.md`.

## Before you finish a change

Run the backend tests and the repo checks; do not finalize with any of these red:

```powershell
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .
uv run python scripts/check_repo.py
```

`scripts/check_repo.py` treats this file as a required contract, so keep it
present and current. When you add a durable rule, put it in the right `docs/`
page and link it from the table above rather than growing this file.

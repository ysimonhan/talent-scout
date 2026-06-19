# Talent Scout

Talent Scout is a fullstack AI sourcing agent demo with a FastAPI
backend, Vite/React frontend, PostgreSQL/pgvector persistence, recruiter
approval gates, and an optional backend-mediated voice outreach path.

This is a sanitized public portfolio case study. It uses synthetic demo data
only and is not connected to any client system, ATS, CRM, or private database.

## Why This Exists

Making agents actually useful means turning a messy business workflow into a system with explicit state, approval checkpoints, tool boundaries, deployment shape, and failure handling.

This repo shows that through a talent sourcing agent workflow:

- a user selects a role briefing in the frontend
- the backend seeds synthetic candidates and role vectors
- pgvector-backed search ranks candidates for the selected role
- deterministic evaluation logic explains fit, risks, and contact channels
- the workflow pauses for recruiter approval before outreach
- voice outreach stays behind backend controls and is disabled by default

## Live Demo

Railway demo: [talentscout-demo.up.railway.app](https://talentscout-demo.up.railway.app)

## Architecture

```text
frontend/ React cockpit
  -> backend/ FastAPI API
  -> PostgreSQL + pgvector
  -> deterministic evaluation and workflow state
  -> optional ElevenLabs/Twilio call path behind backend controls
```

The frontend and backend are deployed as separate Railway services from the
same repository.

## Project Layout

- `backend/`: API, SQLAlchemy models, seed data, search, evaluation, workflow,
  approvals, and voice integration
- `frontend/`: Vite/React recruiter cockpit and Workday-style demo profile page
- `voice/`: ElevenLabs ConvAI project for the optional voice-outreach agent
- `docs/`: architecture, reliability, planning, and integration notes
- `evals/`: smoke scenarios for the project harness
- `scripts/`: repo checks, preflight capture, fixture capture, and harness run

## Quick Start

Install Python dependencies:

```powershell
uv sync
```

Start PostgreSQL with pgvector:

```powershell
docker compose up -d postgres
```

Create local environment config:

```powershell
Copy-Item backend/.env.example .env
```

Start the backend:

```powershell
uv run uvicorn backend.main:app --reload --port 8000
```

Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and calls the backend at
`http://localhost:8000` by default.

## Demo API Flow

1. `POST /api/seed` resets the database and seeds synthetic roles and candidates.
2. `POST /api/analyze` runs role search and deterministic evaluation.
3. `POST /api/approvals/{candidate_id}` approves or declines one candidate.
4. `POST /api/call/{candidate_id}` starts a backend-mediated voice call only
   when live calls are explicitly enabled and credentials are configured.
5. `GET /api/status` returns state, candidates, approvals, outreach actions,
   call logs, and pipeline events.
6. `POST /api/reset` reseeds and resets the workflow.

Supported demo role IDs are `demo-it-pm`, `demo-cloud-architect`, and
`demo-data-engineer`.

## Railway Deployment

Deploy as two Railway services plus one Railway Postgres database.

Backend service:

- Root Directory: `/`
- Config File: `/railway.backend.toml`
- Healthcheck: `GET /api/health`

Frontend service:

- Root Directory: `/frontend`
- Config File: `/railway.frontend.toml`
- Environment variable: `VITE_API_BASE_URL=https://YOUR-BACKEND-DOMAIN`

After both services have public domains, update backend `CORS_ORIGINS` with the
frontend domain and redeploy the backend.

## Verification

```powershell
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .
uv run python scripts/check_repo.py
uv run python scripts/run_harness.py
```

Frontend build:

```powershell
cd frontend
npm install
npm run build
```

## Privacy And Safety

- All role, candidate, and workflow data is synthetic.
- The default voice configuration cannot place live calls.
- Frontend code never receives ElevenLabs or Twilio credentials.
- Outbound calls require backend credentials, `ALLOW_LIVE_CALLS=true`, and a
  recruiter-submitted E.164 phone number.
- Tests mock external voice requests and must never place real calls.

## Current Limitations

- Candidate embeddings are deterministic demo vectors, not production semantic embeddings, yet.
- Evaluation is rule-based and deterministic, not a learned ranking model.
- Workday, Outlook, and LinkedIn data are simulated surfaces.
- Voice outreach is implemented as an optional provider path but should remain
  disabled for public demos unless intentionally tested with safe numbers.

## Roadmap

- Replace deterministic demo vectors with a real embedding and vector ingestion pipeline.
- Add structured fixtures for upstream ATS/CRM/search integrations.
- Add a short Railway demo video or GIF after publish.

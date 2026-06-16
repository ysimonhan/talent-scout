from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db import get_session, init_db
from backend.evaluation import evaluate_candidates
from backend.models import CallLog, CandidateApproval, Job, OutreachAction, PipelineEvent
from backend.outreach import (
    all_top_candidates_decided,
    create_outreach_actions,
    create_pending_approvals,
    list_approvals,
    serialize_approval,
    set_candidate_approval,
)
from backend.search import semantic_search
from backend.seed import reset_and_seed
from backend.state import WorkflowState, get_active_job_id, get_state, set_active_job_id, set_state
from backend.voice import VoiceError, place_outbound_call
from backend.workflow import add_event, transition

app = FastAPI(title="DemoCo AI-First Sourcing Prototype")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApprovalRequest(BaseModel):
    decision: str
    note: str | None = None
    decided_by: str = "demo_recruiter"


class AnalyzeRequest(BaseModel):
    job_id: str = "demo-it-pm"


class CallRequest(BaseModel):
    """Request body for a backend-mediated outbound voice call."""

    target_phone_number: str
    first_message: str | None = None
    recruiter_intro: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


def _events(session: Session) -> list[dict]:
    rows = session.execute(select(PipelineEvent).order_by(PipelineEvent.id)).scalars().all()
    return [
        {
            "id": e.id,
            "step": e.step,
            "status": e.status,
            "message": e.message,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in rows
    ]


def _voice_status() -> dict:
    configured = bool(
        settings.allow_live_calls
        and settings.elevenlabs_api_key
        and settings.elevenlabs_agent_id
        and settings.elevenlabs_agent_phone_number_id
    )
    return {
        "allow_live_calls": settings.allow_live_calls,
        "configured": configured,
        "live_call_ready": configured,
        "target_phone_number_configured": False,
        "elevenlabs_configured": bool(
            settings.elevenlabs_api_key
            and settings.elevenlabs_agent_id
            and settings.elevenlabs_agent_phone_number_id
        ),
    }


def _candidate_is_approved_for_call(session: Session, candidate_id: str) -> bool:
    """Return whether this candidate has individual recruiter approval."""
    approval = session.get(CandidateApproval, candidate_id)
    return bool(approval and approval.decision == "approved")


@app.post("/api/seed")
def seed(session: Session = Depends(get_session)):
    reset_and_seed(session)
    add_event(session, "seed", WorkflowState.seeded.value, "Demo-Daten und Workflow zurückgesetzt.")
    return {"state": get_state(session).value, "message": "Seed completed"}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest | None = None, session: Session = Depends(get_session)):
    set_state(WorkflowState.analyzing, session)
    add_event(
        session, "semantic requirement analysis", "ok", "Anforderungsprofil semantisch aufbereitet."
    )

    job_id = request.job_id if request else "demo-it-pm"
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(
            status_code=400, detail=f"No seeded job found for {job_id}. Run /api/seed first."
        )
    set_active_job_id(job.id, session)

    results = semantic_search(session=session, job=job)
    add_event(session, "pgvector talent-pool search", "ok", "Kandidaten über Vektorsuche gerankt.")

    ranked = evaluate_candidates(results, job.id)
    create_pending_approvals(session, [candidate["id"] for candidate in ranked[:3]])
    add_event(
        session, "simulated evaluation API", "ok", "Deterministische Demo-Bewertung angewendet."
    )
    add_event(
        session,
        "conflict check",
        "blocked",
        "Strategischer Workforce-Planning-Konflikt erkannt. Recruiter-Freigabe erforderlich.",
    )
    transition(
        session,
        WorkflowState.paused_for_recruiter_approval,
        "pause",
        "Pipeline pausiert bis manuelle Freigabe erfolgt.",
    )

    return {
        "state": get_state(session).value,
        "job_id": job.id,
        "voice": _voice_status(),
        "analysis_steps": [
            "Semantic requirement analysis",
            "pgvector talent-pool search",
            "Simulated evaluation API",
            "Conflict check",
            "Pause for recruiter approval",
        ],
        "candidates": ranked,
        "approvals": list_approvals(session),
        "events": _events(session),
    }


@app.post("/api/approve")
def approve(session: Session = Depends(get_session)):
    if get_state(session) != WorkflowState.paused_for_recruiter_approval:
        raise HTTPException(
            status_code=400, detail="Approval only valid from paused_for_recruiter_approval."
        )

    job_id = get_active_job_id(session)
    transition(session, WorkflowState.approved, "approval", "Recruiter approval granted.")
    for approval in list_approvals(session):
        set_candidate_approval(
            session=session,
            candidate_id=approval["candidate_id"],
            decision="approved",
            job_id=job_id,
            note="Global recruiter approval granted.",
        )
    actions = create_outreach_actions(session, job_id)
    transition(session, WorkflowState.outreach_ready, "outreach", "Outreach actions created.")

    return {
        "state": get_state(session).value,
        "job_id": job_id,
        "voice": _voice_status(),
        "approvals": list_approvals(session),
        "outreach_actions": [
            {
                "id": a.id,
                "candidate_id": a.candidate_id,
                "channel": a.channel,
                "status": a.status,
                "message_excerpt": a.message_excerpt,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
    }


@app.post("/api/approvals/{candidate_id}")
def decide_candidate_approval(
    candidate_id: str,
    request: ApprovalRequest,
    session: Session = Depends(get_session),
):
    if get_state(session) not in {
        WorkflowState.paused_for_recruiter_approval,
        WorkflowState.approved,
        WorkflowState.outreach_ready,
        WorkflowState.call_in_progress,
        WorkflowState.call_completed,
    }:
        raise HTTPException(
            status_code=400,
            detail="Candidate approvals are valid only after analysis pauses for recruiter approval.",
        )

    job_id = get_active_job_id(session)
    try:
        approval = set_candidate_approval(
            session=session,
            candidate_id=candidate_id,
            decision=request.decision,
            job_id=job_id,
            note=request.note,
            decided_by=request.decided_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    add_event(
        session,
        "candidate approval",
        approval.decision,
        f"{candidate_id} marked {approval.decision} by recruiter.",
    )

    if all_top_candidates_decided(session):
        transition(
            session,
            WorkflowState.outreach_ready,
            "outreach",
            "All top candidates decided; outreach actions are ready.",
        )

    actions = session.execute(select(OutreachAction).order_by(OutreachAction.id)).scalars().all()
    return {
        "state": get_state(session).value,
        "job_id": job_id,
        "voice": _voice_status(),
        "approval": serialize_approval(approval),
        "approvals": list_approvals(session),
        "outreach_actions": [
            {
                "id": a.id,
                "candidate_id": a.candidate_id,
                "channel": a.channel,
                "status": a.status,
                "message_excerpt": a.message_excerpt,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
    }


@app.post("/api/call/{candidate_id}")
def call(
    candidate_id: str, request: CallRequest | None = None, session: Session = Depends(get_session)
):
    previous_state = get_state(session)
    if previous_state not in {
        WorkflowState.paused_for_recruiter_approval,
        WorkflowState.outreach_ready,
        WorkflowState.call_in_progress,
        WorkflowState.call_completed,
    }:
        raise HTTPException(status_code=400, detail="Calls allowed only after candidate approval.")
    if not _candidate_is_approved_for_call(session, candidate_id):
        raise HTTPException(
            status_code=400, detail="Calls allowed only after this candidate is approved."
        )
    if request is None:
        raise HTTPException(
            status_code=400, detail="target_phone_number is required in the request body."
        )

    set_state(WorkflowState.call_in_progress, session)
    add_event(
        session,
        "call",
        WorkflowState.call_in_progress.value,
        f"Attempting call for {candidate_id}.",
    )
    try:
        result = place_outbound_call(
            session=session,
            candidate_id=candidate_id,
            target_phone_number=request.target_phone_number,
            first_message=request.first_message,
            recruiter_intro=request.recruiter_intro,
        )
    except VoiceError as exc:
        session.rollback()
        set_state(previous_state, session)
        add_event(session, "call", WorkflowState.error.value, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        session.rollback()
        set_state(previous_state, session)
        add_event(session, "call", WorkflowState.error.value, f"Unexpected voice error: {exc}")
        raise HTTPException(status_code=502, detail="Voice provider call failed") from exc

    set_state(WorkflowState.call_completed, session)
    add_event(session, "call", WorkflowState.call_completed.value, "Call completed request cycle.")
    return {"state": get_state(session).value, **result}


@app.get("/api/status")
def status(session: Session = Depends(get_session)):
    job_id = get_active_job_id(session)
    job = session.get(Job, job_id)
    candidates = (
        evaluate_candidates(semantic_search(session=session, job=job, limit=6), job_id)
        if job
        else []
    )
    actions = session.execute(select(OutreachAction).order_by(OutreachAction.id)).scalars().all()
    calls = session.execute(select(CallLog).order_by(CallLog.id)).scalars().all()
    return {
        "state": get_state(session).value,
        "job_id": job_id,
        "voice": _voice_status(),
        "candidates": candidates,
        "approvals": list_approvals(session),
        "outreach_actions": [
            {
                "id": a.id,
                "candidate_id": a.candidate_id,
                "channel": a.channel,
                "status": a.status,
                "message_excerpt": a.message_excerpt,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
        "call_logs": [
            {
                "id": c.id,
                "candidate_id": c.candidate_id,
                "callSid": c.call_sid,
                "conversation_id": c.conversation_id,
                "status": c.status,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in calls
        ],
        "events": _events(session),
    }


@app.post("/api/reset")
def reset(session: Session = Depends(get_session)):
    reset_and_seed(session)
    add_event(
        session, "reset", WorkflowState.seeded.value, "Workflow reset and demo data reseeded."
    )
    return {"state": get_state(session).value, "message": "Reset complete."}

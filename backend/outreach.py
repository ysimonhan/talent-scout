from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.evaluation import outreach_channel_for
from backend.models import CandidateApproval, OutreachAction


OUTREACH_PLAN = [
    {
        "candidate_id": "katharina",
        "channel": "linkedin_inmail",
        "status": "sent",
        "message_excerpt": "Hallo Katharina, wir sehen starken Fit auf die IT-Projektmanager-Rolle.",
    },
    {
        "candidate_id": "daniel",
        "channel": "linkedin_inmail",
        "status": "sent",
        "message_excerpt": "Hallo Daniel, Ihr SAFe-/Infrastrukturprofil passt sehr gut zu DemoCo.",
    },
    {
        "candidate_id": "miriam",
        "channel": "voice_call",
        "status": "ready",
        "message_excerpt": "Miriam S. priorisiert für telefonische Ansprache.",
    },
]


def create_pending_approvals(session: Session, candidate_ids: list[str]) -> list[CandidateApproval]:
    approvals: list[CandidateApproval] = []
    for candidate_id in candidate_ids:
        approval = session.get(CandidateApproval, candidate_id)
        if approval is None:
            approval = CandidateApproval(candidate_id=candidate_id, decision="pending")
            session.add(approval)
        approvals.append(approval)
    session.commit()
    for approval in approvals:
        session.refresh(approval)
    return approvals


def serialize_approval(approval: CandidateApproval) -> dict:
    return {
        "candidate_id": approval.candidate_id,
        "decision": approval.decision,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
        "decided_by": approval.decided_by,
        "note": approval.note,
    }


def list_approvals(session: Session) -> list[dict]:
    rows = (
        session.execute(select(CandidateApproval).order_by(CandidateApproval.candidate_id))
        .scalars()
        .all()
    )
    return [serialize_approval(row) for row in rows]


def _plan_for_candidate(candidate_id: str, job_id: str = "demo-it-pm") -> dict | None:
    channel = outreach_channel_for(job_id, candidate_id)
    if channel == "none":
        return None

    if candidate_id == "miriam" and channel == "voice_call":
        return {
            "candidate_id": candidate_id,
            "channel": "voice_call",
            "status": "ready",
            "message_excerpt": "Miriam S. priorisiert für telefonische Ansprache.",
        }

    return next((item for item in OUTREACH_PLAN if item["candidate_id"] == candidate_id), None)


def _existing_action(session: Session, candidate_id: str) -> OutreachAction | None:
    return session.execute(
        select(OutreachAction).where(OutreachAction.candidate_id == candidate_id)
    ).scalar_one_or_none()


def create_outreach_action_for_candidate(
    session: Session, candidate_id: str, job_id: str = "demo-it-pm"
) -> OutreachAction | None:
    channel = outreach_channel_for(job_id, candidate_id)
    if channel == "none":
        return None

    plan = _plan_for_candidate(candidate_id, job_id)
    if plan is None:
        plan = {
            "candidate_id": candidate_id,
            "channel": channel,
            "status": "sent",
            "message_excerpt": f"{candidate_id} für Outreach freigegeben.",
        }

    existing = _existing_action(session, candidate_id)
    if existing is not None:
        return existing

    action = OutreachAction(
        candidate_id=plan["candidate_id"],
        channel=plan["channel"],
        status=plan["status"],
        message_excerpt=plan["message_excerpt"],
        created_at=datetime.utcnow(),
    )
    session.add(action)
    session.commit()
    session.refresh(action)
    return action


def set_candidate_approval(
    session: Session,
    candidate_id: str,
    decision: str,
    job_id: str = "demo-it-pm",
    note: str | None = None,
    decided_by: str = "demo_recruiter",
) -> CandidateApproval:
    if decision not in {"approved", "declined"}:
        raise ValueError("decision must be approved or declined.")

    approval = session.get(CandidateApproval, candidate_id)
    if approval is None:
        raise ValueError("Candidate is not pending approval for the current sourcing run.")

    approval.decision = decision
    approval.note = note
    approval.decided_by = decided_by
    approval.decided_at = datetime.utcnow()
    session.commit()
    session.refresh(approval)

    if decision == "approved":
        create_outreach_action_for_candidate(session, candidate_id, job_id)

    return approval


def all_top_candidates_decided(session: Session) -> bool:
    approvals = session.execute(select(CandidateApproval)).scalars().all()
    return bool(approvals) and all(
        approval.decision in {"approved", "declined"} for approval in approvals
    )


def create_outreach_actions(session: Session, job_id: str = "demo-it-pm") -> list[OutreachAction]:
    actions: list[OutreachAction] = []
    approvals = session.execute(select(CandidateApproval)).scalars().all()
    for approval in approvals:
        if approval.decision != "approved":
            continue
        action = create_outreach_action_for_candidate(session, approval.candidate_id, job_id)
        if action is not None:
            actions.append(action)
    return actions

from enum import Enum
from datetime import datetime


class WorkflowState(str, Enum):
    idle = "idle"
    seeded = "seeded"
    analyzing = "analyzing"
    paused_for_recruiter_approval = "paused_for_recruiter_approval"
    approved = "approved"
    outreach_ready = "outreach_ready"
    call_in_progress = "call_in_progress"
    call_completed = "call_completed"
    error = "error"


_current_state: WorkflowState = WorkflowState.idle


def get_state(session=None) -> WorkflowState:
    if session is not None:
        from backend.models import WorkflowStatus

        row = session.get(WorkflowStatus, "current")
        if row:
            return WorkflowState(row.state)
    return _current_state


def set_state(state: WorkflowState, session=None) -> WorkflowState:
    global _current_state
    _current_state = state
    if session is not None and hasattr(session, "add") and hasattr(session, "commit"):
        from backend.models import WorkflowStatus

        row = session.get(WorkflowStatus, "current")
        if row is None:
            row = WorkflowStatus(id="current", state=state.value, updated_at=datetime.utcnow())
            session.add(row)
        else:
            row.state = state.value
            row.updated_at = datetime.utcnow()
        session.commit()
    return _current_state


def get_active_job_id(session=None) -> str:
    if session is not None:
        from backend.models import WorkflowStatus

        row = session.get(WorkflowStatus, "current")
        if row and row.job_id:
            return row.job_id
    return "demo-it-pm"


def set_active_job_id(job_id: str, session) -> str:
    from backend.models import WorkflowStatus

    row = session.get(WorkflowStatus, "current")
    if row is None:
        row = WorkflowStatus(
            id="current",
            state=_current_state.value,
            job_id=job_id,
            updated_at=datetime.utcnow(),
        )
        session.add(row)
    else:
        row.job_id = job_id
        row.updated_at = datetime.utcnow()
    session.commit()
    return job_id

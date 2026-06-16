from datetime import datetime

from sqlalchemy.orm import Session

from backend.models import PipelineEvent
from backend.state import WorkflowState, get_state, set_state


def add_event(session: Session, step: str, status: str, message: str) -> PipelineEvent:
    event = PipelineEvent(step=step, status=status, message=message, timestamp=datetime.utcnow())
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def transition(session: Session, state: WorkflowState, step: str, message: str) -> WorkflowState:
    set_state(state, session)
    add_event(session=session, step=step, status=state.value, message=message)
    return get_state(session)

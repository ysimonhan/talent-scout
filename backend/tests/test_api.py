from fastapi.testclient import TestClient

from backend.main import app
from backend.state import WorkflowState, set_state


class DummySession:
    def get(self, model, key):
        if key == "demo-it-pm":
            return type("Job", (), {"id": "demo-it-pm"})()
        return None


class CallSession:
    def __init__(self, state=WorkflowState.paused_for_recruiter_approval, approved=True):
        self.workflow = type("Workflow", (), {"state": state.value, "job_id": "demo-it-pm"})()
        self.approval = (
            type("Approval", (), {"candidate_id": "miriam", "decision": "approved"})()
            if approved
            else None
        )
        self.rollback_called = False

    def get(self, model, key):
        if model.__name__ == "WorkflowStatus" and key == "current":
            return self.workflow
        if model.__name__ == "CandidateApproval" and key == "miriam":
            return self.approval
        return None

    def add(self, item):
        return None

    def commit(self):
        return None

    def rollback(self):
        self.rollback_called = True


def test_analyze_pauses_for_approval(monkeypatch):
    app.router.on_startup.clear()
    dummy = DummySession()

    from backend import main as backend_main

    app.dependency_overrides[backend_main.get_session] = lambda: dummy
    monkeypatch.setattr(backend_main, "add_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(backend_main, "_events", lambda session: [])
    monkeypatch.setattr(backend_main, "create_pending_approvals", lambda session, candidate_ids: [])
    monkeypatch.setattr(backend_main, "set_active_job_id", lambda job_id, session: job_id)
    monkeypatch.setattr(backend_main, "list_approvals", lambda session: [])

    def fake_transition(session, state, step, message):
        set_state(state)
        return state

    monkeypatch.setattr(backend_main, "transition", fake_transition)
    monkeypatch.setattr(
        backend_main,
        "semantic_search",
        lambda session, job: [
            {
                "candidate": type(
                    "Candidate",
                    (),
                    {
                        "id": "katharina",
                        "name": "Katharina B.",
                        "source": "LinkedIn",
                        "descriptor": "PRINCE2 · 7J. Energiebranche",
                        "fixed_score": 91,
                        "channel": "linkedin_inmail",
                        "qualified": True,
                        "rationale": "Fit",
                    },
                )(),
                "vector_similarity": 0.94,
            }
        ],
    )

    client = TestClient(app)
    response = client.post("/api/analyze")
    assert response.status_code == 200
    assert response.json()["state"] == WorkflowState.paused_for_recruiter_approval.value


def test_call_requires_approval(monkeypatch):
    app.router.on_startup.clear()
    dummy = DummySession()
    from backend import main as backend_main

    app.dependency_overrides[backend_main.get_session] = lambda: dummy
    monkeypatch.setattr(backend_main, "add_event", lambda *args, **kwargs: None)
    set_state(WorkflowState.seeded)

    client = TestClient(app)
    response = client.post("/api/call/miriam")
    assert response.status_code == 400
    assert "candidate approval" in response.json()["detail"]


def test_call_allowed_after_single_candidate_approval(monkeypatch):
    app.router.on_startup.clear()
    session = CallSession()
    from backend import main as backend_main

    app.dependency_overrides[backend_main.get_session] = lambda: session
    monkeypatch.setattr(backend_main, "add_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        backend_main,
        "place_outbound_call",
        lambda **kwargs: {
            "candidate_id": "miriam",
            "status": "initiated",
            "callSid": "CA123",
            "conversation_id": "conv_123",
            "message": "Call request submitted.",
        },
    )

    client = TestClient(app)
    response = client.post("/api/call/miriam", json={"target_phone_number": "+491000000000"})

    assert response.status_code == 200
    assert response.json()["state"] == WorkflowState.call_completed.value
    assert response.json()["callSid"] == "CA123"


def test_call_error_rolls_back_and_keeps_retryable_state(monkeypatch):
    app.router.on_startup.clear()
    session = CallSession()
    from backend import main as backend_main

    app.dependency_overrides[backend_main.get_session] = lambda: session
    monkeypatch.setattr(backend_main, "add_event", lambda *args, **kwargs: None)

    def fail_call(**kwargs):
        raise backend_main.VoiceError("Network access error")

    monkeypatch.setattr(backend_main, "place_outbound_call", fail_call)

    client = TestClient(app)
    response = client.post("/api/call/miriam", json={"target_phone_number": "+491000000000"})

    assert response.status_code == 502
    assert session.rollback_called is True
    assert session.workflow.state == WorkflowState.paused_for_recruiter_approval.value

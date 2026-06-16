import pytest

from backend import voice
from backend.models import Candidate, Job
from backend.seed import DEMO_CANDIDATES, DEMO_JOBS
from backend.voice import (
    VoiceError,
    build_voice_context,
    normalize_phone_number,
    place_outbound_call,
)


class DummySession:
    """Minimal SQLAlchemy session double for call-log persistence tests."""

    def __init__(self, job_id: str = "demo-it-pm") -> None:
        self.added: list[object] = []
        self.candidates = {
            item["id"]: Candidate(
                **{key: value for key, value in item.items() if key != "embedding"}
            )
            for item in DEMO_CANDIDATES
        }
        self.jobs = {item["id"]: Job(**item) for item in DEMO_JOBS}
        self.workflow = type("Workflow", (), {"job_id": job_id})()

    def add(self, item: object) -> None:
        """Record the item that would have been persisted."""
        self.added.append(item)

    def get(self, model, key):
        """Return seeded demo rows needed by the voice context builder."""
        if model.__name__ == "Candidate":
            return self.candidates.get(key)
        if model.__name__ == "Job":
            return self.jobs.get(key)
        if model.__name__ == "WorkflowStatus" and key == "current":
            return self.workflow
        return None

    def commit(self) -> None:
        """Simulate committing a transaction."""

    def refresh(self, item: object) -> None:
        """Simulate refreshing a persisted model."""


class DummyResponse:
    """Requests response double for voice-provider tests."""

    def __init__(self, ok: bool, payload: dict, status_code: int = 200) -> None:
        self.ok = ok
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self) -> dict:
        """Return the configured response payload."""
        return self._payload


def _enable_live_voice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure voice settings for mocked live-call tests."""
    monkeypatch.setattr(voice.settings, "allow_live_calls", True)
    monkeypatch.setattr(voice.settings, "elevenlabs_api_key", "test-key")
    monkeypatch.setattr(voice.settings, "elevenlabs_agent_id", "test-agent")
    monkeypatch.setattr(voice.settings, "elevenlabs_agent_phone_number_id", "test-phone-id")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+491000000000", "+491000000000"),
        ("+49 1000 000000", "+491000000000"),
        ("0049 1000 000000", "+491000000000"),
        ("+49 (1000) 000-000", "+491000000000"),
    ],
)
def test_normalize_phone_number_accepts_e164_variants(raw: str, expected: str) -> None:
    assert normalize_phone_number(raw) == expected


@pytest.mark.parametrize("raw", ["", "017657961651", "+49abc", "+012345678"])
def test_normalize_phone_number_rejects_non_e164_numbers(raw: str) -> None:
    with pytest.raises(VoiceError, match="E.164"):
        normalize_phone_number(raw)


def test_place_outbound_call_sends_overwritten_number(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_live_voice(monkeypatch)
    captured_request: dict = {}

    def fake_post(*args, **kwargs) -> DummyResponse:
        """Capture the provider request without placing a live call."""
        captured_request.update(kwargs)
        return DummyResponse(
            ok=True,
            payload={"success": True, "callSid": "CA123", "conversation_id": "conv_123"},
        )

    monkeypatch.setattr(voice.requests, "post", fake_post)

    result = place_outbound_call(
        session=DummySession(),
        candidate_id="miriam",
        target_phone_number="+49 1000 000000",
        recruiter_intro="Hallo Miriam, hier ist Laura von DemoCo.",
    )

    provider_payload = captured_request["json"]
    dynamic_variables = provider_payload["conversation_initiation_client_data"]["dynamic_variables"]
    assert provider_payload["to_number"] == "+491000000000"
    assert "conversation_config_override" not in provider_payload
    assert dynamic_variables["candidate_name"] == "Miriam S."
    assert dynamic_variables["role_title"] == "IT-Projektmanager (m/w/d)"
    assert dynamic_variables["recruiter_intro"] == "Hallo Miriam, hier ist Laura von DemoCo."
    assert result["callSid"] == "CA123"


@pytest.mark.parametrize(
    ("candidate_id", "job_id", "expected_name", "expected_role", "expected_rationale"),
    [
        ("miriam", "demo-it-pm", "Miriam S.", "IT-Projektmanager", "PMP"),
        ("miriam", "demo-data-engineer", "Miriam S.", "Data Engineer", "datengetriebene"),
        ("daniel", "demo-it-pm", "Daniel W.", "IT-Projektmanager", "SAFe"),
        ("daniel", "demo-cloud-architect", "Daniel W.", "Cloud Architect", "Infrastrukturführung"),
    ],
)
def test_build_voice_context_uses_candidate_and_role_demo_data(
    candidate_id: str,
    job_id: str,
    expected_name: str,
    expected_role: str,
    expected_rationale: str,
) -> None:
    context = build_voice_context(
        session=DummySession(job_id=job_id),
        candidate_id=candidate_id,
        recruiter_intro="Manuell geschriebener Introtext.",
    )

    assert context["candidate_name"] == expected_name
    assert expected_role in context["role_title"]
    assert expected_rationale in context["role_fit_rationale"]
    assert context["candidate_source"]
    assert context["candidate_descriptor"]
    assert context["candidate_context"]
    assert context["prior_interactions"].startswith("- ")
    assert context["role_requirements"]
    assert context["recruiter_intro"] == "Manuell geschriebener Introtext."


def test_build_voice_context_omits_compensation_wording() -> None:
    context = build_voice_context(
        session=DummySession(),
        candidate_id="miriam",
        recruiter_intro=(
            "Hallo Miriam, hier ist Laura von DemoCo. "
            "Das Gehalt und die Compensation besprechen wir sofort."
        ),
    )

    flattened_context = "\n".join(context.keys()) + "\n" + "\n".join(context.values())
    assert "compensation" not in flattened_context.lower()
    assert "gehalt" not in flattened_context.lower()
    assert "salary" not in flattened_context.lower()


def test_place_outbound_call_rejects_invalid_number_before_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_voice(monkeypatch)
    provider_called = False

    def fake_post(*args, **kwargs) -> DummyResponse:
        """Fail the test if validation lets an invalid number reach the provider."""
        nonlocal provider_called
        provider_called = True
        return DummyResponse(ok=True, payload={})

    monkeypatch.setattr(voice.requests, "post", fake_post)

    with pytest.raises(VoiceError, match="E.164"):
        place_outbound_call(
            session=DummySession(),
            candidate_id="miriam",
            target_phone_number="017657961651",
        )

    assert provider_called is False


def test_provider_network_access_error_mentions_telephony_permissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_voice(monkeypatch)

    def fake_post(*args, **kwargs) -> DummyResponse:
        """Return the kind of provider error surfaced for blocked destinations."""
        return DummyResponse(
            ok=False,
            status_code=422,
            payload={"detail": "Network access error", "code": 21215},
        )

    monkeypatch.setattr(voice.requests, "post", fake_post)

    with pytest.raises(VoiceError, match="Geo Permissions"):
        place_outbound_call(
            session=DummySession(),
            candidate_id="miriam",
            target_phone_number="+491000000000",
        )


def test_provider_http_ok_failure_raises_without_null_call_log(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_voice(monkeypatch)
    session = DummySession()

    def fake_post(*args, **kwargs) -> DummyResponse:
        """Return an HTTP-ok provider failure with null provider IDs."""
        return DummyResponse(
            ok=True,
            status_code=200,
            payload={
                "success": False,
                "callSid": None,
                "conversation_id": None,
                "message": "Network access error",
                "code": 21215,
            },
        )

    monkeypatch.setattr(voice.requests, "post", fake_post)

    with pytest.raises(VoiceError, match="Geo Permissions"):
        place_outbound_call(
            session=session,
            candidate_id="miriam",
            target_phone_number="+491000000000",
        )

    assert len(session.added) == 1
    assert session.added[0].call_sid == "unknown"
    assert session.added[0].conversation_id == "unknown"
    assert session.added[0].status == "failed"

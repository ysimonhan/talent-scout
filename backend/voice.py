import re
from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from backend.config import settings
from backend.evaluation import ROLE_EVALUATIONS, contact_profile_for
from backend.models import CallLog, Candidate, Job
from backend.state import get_active_job_id

GERMAN_CALL_SCRIPT = (
    "Hallo {candidate_name}, hier ist Laura von Demo Recruiting. Ich melde mich, weil Ihr "
    "Profil gut zur Rolle {role_title} passt. Haben Sie kurz Zeit für einen ersten Austausch?"
)

VOICE_ENABLED_CANDIDATE_IDS = {"daniel", "miriam"}
E164_PHONE_NUMBER_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
COMPENSATION_TERMS = (
    "bonus",
    "compensation",
    "gehalt",
    "benefits",
    "salary",
    "verguetung",
    "vergütung",
)


class VoiceError(ValueError):
    """Raised when a voice call cannot be submitted safely."""

    pass


def normalize_phone_number(target_phone_number: str) -> str:
    """Normalize a recruiter-submitted phone number to strict E.164 format."""
    phone_number = target_phone_number.strip()
    if phone_number.startswith("00"):
        phone_number = f"+{phone_number[2:]}"
    phone_number = re.sub(r"[\s().-]", "", phone_number)

    if not E164_PHONE_NUMBER_PATTERN.fullmatch(phone_number):
        raise VoiceError(
            "target_phone_number must use international E.164 format, e.g. +491000000000."
        )
    return phone_number


def _stringify_provider_payload(payload: Any) -> str:
    """Extract the useful human-readable bits from nested provider error payloads."""
    if isinstance(payload, dict):
        parts: list[str] = []
        for key in ("message", "detail", "error", "reason", "code", "status"):
            value = payload.get(key)
            if value is None:
                continue
            if isinstance(value, dict | list):
                parts.append(f"{key}={_stringify_provider_payload(value)}")
            else:
                parts.append(f"{key}={value}")
        return "; ".join(parts) or str(payload)[:500]
    if isinstance(payload, list):
        return "; ".join(_stringify_provider_payload(item) for item in payload[:3])
    return str(payload)[:500]


def _provider_error_hint(provider_message: str) -> str:
    """Return an operator hint for common Twilio errors surfaced through ElevenLabs."""
    normalized = provider_message.lower()
    if (
        "21215" in normalized
        or "geo permission" in normalized
        or "network access" in normalized
        or "not permitting call" in normalized
    ):
        return (
            " This is usually a Twilio/ElevenLabs telephony permission issue, not a browser "
            "network issue. Enable the destination country/range in Twilio Geo Permissions "
            "or allow/verify the destination number in the connected Twilio account."
        )
    if "21219" in normalized or ("to" in normalized and "not verified" in normalized):
        return (
            " Twilio trial accounts can only call verified destination numbers; verify this "
            "recipient number or upgrade the connected Twilio account."
        )
    return ""


def _provider_error_message(response: requests.Response) -> str:
    """Create a concise error message without exposing request credentials."""
    try:
        payload = response.json()
    except ValueError:
        payload = response.text[:500]
    provider_message = _stringify_provider_payload(payload)
    return (
        f"ElevenLabs call failed with HTTP {response.status_code}: {provider_message}"
        f"{_provider_error_hint(provider_message)}"
    )


def _provider_payload_value(payload: dict, *keys: str, fallback: str) -> str:
    """Read a non-empty string value from a provider payload."""
    for key in keys:
        value = payload.get(key)
        if value:
            return str(value)
    return fallback


def _provider_payload_failure_message(payload: dict) -> str:
    """Create a VoiceError message from an HTTP-ok provider failure payload."""
    provider_message = _stringify_provider_payload(payload)
    return (
        f"ElevenLabs call was not initiated: {provider_message}"
        f"{_provider_error_hint(provider_message)}"
    )


def _strip_compensation_sentences(text: str) -> str:
    """Remove sentences that contain compensation wording from voice-agent input."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    safe_parts = [
        part
        for part in parts
        if part and not any(term in part.lower() for term in COMPENSATION_TERMS)
    ]
    return " ".join(safe_parts).strip()


def _safe_value(value: str, fallback: str) -> str:
    """Return a non-empty dynamic-variable value with compensation wording removed."""
    safe = _strip_compensation_sentences(value)
    return safe or fallback


def _format_prior_interactions(candidate_id: str) -> str:
    """Format existing demo interaction facts for the voice agent."""
    interactions = contact_profile_for(candidate_id)["interaction_summary"]
    if not interactions:
        return "Keine früheren Interaktionen im Demo-Datensatz."
    return "\n".join(f"- {item}" for item in interactions)


def _role_fit_rationale(candidate: Candidate, job_id: str) -> str:
    """Return the deterministic demo rationale for this candidate and role."""
    role_evaluation = ROLE_EVALUATIONS.get(job_id, {}).get(candidate.id)
    if role_evaluation:
        return str(role_evaluation["rationale"])
    return candidate.rationale


def _default_recruiter_intro(candidate: Candidate, job: Job) -> str:
    """Build the safe fallback intro if the recruiter has not edited one."""
    return GERMAN_CALL_SCRIPT.format(candidate_name=candidate.name, role_title=job.title)


def build_voice_context(
    session: Session,
    candidate_id: str,
    recruiter_intro: str | None = None,
    job_id: str | None = None,
) -> dict[str, str]:
    """Assemble ElevenLabs dynamic variables from existing deterministic demo data."""
    candidate = session.get(Candidate, candidate_id)
    if candidate is None:
        raise VoiceError(f"No seeded candidate found for {candidate_id}. Run /api/seed first.")

    active_job_id = job_id or get_active_job_id(session)
    job = session.get(Job, active_job_id)
    if job is None:
        raise VoiceError(f"No seeded job found for {active_job_id}. Run /api/seed first.")

    fallback = "Das Team hat dazu nur begrenzte Informationen im Demo-Datensatz."
    candidate_context = (
        f"Quelle: {candidate.source}. Profilhinweis: {candidate.descriptor}. "
        f"Profilkontext: {candidate.profile_text}"
    )
    role_requirements = "; ".join(job.requirements)
    intro = recruiter_intro.strip() if recruiter_intro else _default_recruiter_intro(candidate, job)

    return {
        "candidate_name": _safe_value(candidate.name, fallback),
        "candidate_source": _safe_value(candidate.source, fallback),
        "candidate_descriptor": _safe_value(candidate.descriptor, fallback),
        "candidate_context": _safe_value(candidate_context, fallback),
        "prior_interactions": _safe_value(_format_prior_interactions(candidate.id), fallback),
        "role_title": _safe_value(job.title, fallback),
        "role_requirements": _safe_value(role_requirements, fallback),
        "role_fit_rationale": _safe_value(_role_fit_rationale(candidate, active_job_id), fallback),
        "recruiter_intro": _safe_value(intro, _default_recruiter_intro(candidate, job)),
    }


def place_outbound_call(
    session: Session,
    candidate_id: str,
    target_phone_number: str,
    first_message: str | None = None,
    recruiter_intro: str | None = None,
) -> dict:
    """Submit an outbound voice call request through the backend-only provider boundary."""
    if candidate_id not in VOICE_ENABLED_CANDIDATE_IDS:
        raise VoiceError("Voice Call is available only for voice-enabled demo candidates.")
    if not settings.allow_live_calls:
        raise VoiceError("Live calls are disabled. Set ALLOW_LIVE_CALLS=true to enable.")
    if not target_phone_number:
        raise VoiceError("target_phone_number is required in the request body.")
    if (
        not settings.elevenlabs_api_key
        or not settings.elevenlabs_agent_id
        or not settings.elevenlabs_agent_phone_number_id
    ):
        raise VoiceError(
            "Missing ElevenLabs credentials. Set API key, agent ID, and phone number ID."
        )

    normalized_phone_number = normalize_phone_number(target_phone_number)
    dynamic_variables = build_voice_context(
        session=session,
        candidate_id=candidate_id,
        recruiter_intro=recruiter_intro or first_message,
    )
    response = requests.post(
        "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
        headers={"xi-api-key": settings.elevenlabs_api_key, "Content-Type": "application/json"},
        json={
            "agent_id": settings.elevenlabs_agent_id,
            "agent_phone_number_id": settings.elevenlabs_agent_phone_number_id,
            "to_number": normalized_phone_number,
            "conversation_initiation_client_data": {
                "dynamic_variables": dynamic_variables,
            },
        },
        timeout=20,
    )
    if not response.ok:
        raise VoiceError(_provider_error_message(response))

    payload = response.json()
    call_sid = _provider_payload_value(payload, "callSid", "call_sid", "sid", fallback="unknown")
    conversation_id = _provider_payload_value(
        payload,
        "conversation_id",
        "conversationId",
        fallback="unknown",
    )
    provider_success = payload.get("success")

    log = CallLog(
        candidate_id=candidate_id,
        call_sid=call_sid,
        conversation_id=conversation_id,
        status="failed" if provider_success is False else "initiated",
        timestamp=datetime.utcnow(),
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    if provider_success is False:
        raise VoiceError(_provider_payload_failure_message(payload))

    return {
        "candidate_id": candidate_id,
        "status": log.status,
        "callSid": log.call_sid,
        "conversation_id": log.conversation_id,
        "message": payload.get("message", "Call request submitted."),
    }

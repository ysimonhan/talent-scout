from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from backend.models import (
    Candidate,
    CandidateApproval,
    CandidateVector,
    CallLog,
    Job,
    JobCandidateVector,
    OutreachAction,
    PipelineEvent,
    WorkflowStatus,
)
from backend.state import WorkflowState, set_active_job_id, set_state

DEMO_JOBS = [
    {
        "id": "demo-it-pm",
        "title": "IT-Projektmanager (m/w/d)",
        "company": "Demo Energy AG",
        "requirements": [
            "4+ Jahre Projektleitung",
            "PRINCE2 or SAFe",
            "Energie / Infrastruktur",
            "Stakeholder Management",
            "Reporting",
            "Hohe Ownership",
        ],
    },
    {
        "id": "demo-cloud-architect",
        "title": "Cloud Architect (m/w/d)",
        "company": "Demo Energy AG · IT Infrastructure",
        "requirements": [
            "Azure / AWS Architektur",
            "Kubernetes",
            "Security und Governance",
            "Regulierte Infrastruktur",
            "Migration kritischer Workloads",
        ],
    },
    {
        "id": "demo-data-engineer",
        "title": "Data Engineer Smart Grid (m/w/d)",
        "company": "Demo Energy AG · Grid Operations",
        "requirements": [
            "Python",
            "dbt / Airflow",
            "IoT- und Energiedaten",
            "Datenplattformen",
            "Schnittstelle Engineering und BI",
        ],
    },
]

DEMO_CANDIDATES = [
    {
        "id": "katharina",
        "name": "Katharina B.",
        "source": "LinkedIn",
        "descriptor": "PRINCE2 · 7J. Energiebranche",
        "profile_text": "Experienced IT project manager with PRINCE2 certification, seven years in energy-sector transformation projects, strong stakeholder management and reporting experience.",
        "fixed_score": 91,
        "fixed_similarity": 0.94,
        "channel": "linkedin_inmail",
        "qualified": True,
        "rationale": "Sehr hoher Fit durch PRINCE2, Energiebranche und mehrjährige Projektleitung.",
        "embedding": [0.94, 0.18, 0.21, 0.19],
    },
    {
        "id": "daniel",
        "name": "Daniel W.",
        "source": "LinkedIn",
        "descriptor": "SAFe Agilist · IT-Leiter Infrastruktur",
        "profile_text": "Infrastructure IT lead, SAFe Agilist, experienced in utility infrastructure, cross-functional technology teams and stakeholder-heavy transformation initiatives.",
        "fixed_score": 85,
        "fixed_similarity": 0.89,
        "channel": "linkedin_inmail",
        "qualified": True,
        "rationale": "Hoher Fit durch SAFe, IT-Infrastruktur und Führungsnähe.",
        "embedding": [0.89, 0.27, 0.26, 0.24],
    },
    {
        "id": "miriam",
        "name": "Miriam S.",
        "source": "Workday Initiativ",
        "descriptor": "PMP · Großprojekte Stakeholder-Mgmt.",
        "profile_text": "Initiativbewerberin with PMP certification, large-scale transformation experience, stakeholder management and strong project governance exposure.",
        "fixed_score": 83,
        "fixed_similarity": 0.86,
        "channel": "voice_call",
        "qualified": True,
        "rationale": "Guter Fit durch PMP, Großprojekterfahrung und Stakeholder-Management. Für Voice Outreach priorisiert.",
        "embedding": [0.86, 0.32, 0.28, 0.25],
    },
    {
        "id": "oliver",
        "name": "Oliver T.",
        "source": "Outlook",
        "descriptor": "Kein Branchenbezug",
        "profile_text": "General project management profile with limited energy, infrastructure or IT project management background.",
        "fixed_score": 62,
        "fixed_similarity": 0.61,
        "channel": "none",
        "qualified": False,
        "rationale": "Teilweiser Projektmanagement-Fit, aber fehlender Branchen- und IT-Bezug.",
        "embedding": [0.61, 0.46, 0.41, 0.3],
    },
    {
        "id": "stefan",
        "name": "Stefan M.",
        "source": "LinkedIn",
        "descriptor": "Kein IT-Hintergrund",
        "profile_text": "Business operations profile without relevant IT project management or technical infrastructure background.",
        "fixed_score": 54,
        "fixed_similarity": 0.52,
        "channel": "none",
        "qualified": False,
        "rationale": "Zu geringe Nähe zur IT-Projektmanager-Rolle.",
        "embedding": [0.52, 0.49, 0.44, 0.34],
    },
    {
        "id": "petra",
        "name": "Petra F.",
        "source": "Workday Archiv",
        "descriptor": "Veraltetes Profil",
        "profile_text": "Archived applicant profile with outdated project experience and insufficient recent information.",
        "fixed_score": 46,
        "fixed_similarity": 0.44,
        "channel": "none",
        "qualified": False,
        "rationale": "Profil ist veraltet und fachlich zu unspezifisch.",
        "embedding": [0.44, 0.56, 0.39, 0.32],
    },
]

ROLE_SIMILARITIES = {
    "demo-it-pm": {
        "katharina": 0.94,
        "daniel": 0.89,
        "miriam": 0.86,
        "oliver": 0.61,
        "stefan": 0.52,
        "petra": 0.44,
    },
    "demo-cloud-architect": {
        "daniel": 0.93,
        "stefan": 0.81,
        "katharina": 0.67,
        "miriam": 0.58,
        "oliver": 0.46,
        "petra": 0.35,
    },
    "demo-data-engineer": {
        "miriam": 0.84,
        "petra": 0.72,
        "daniel": 0.64,
        "katharina": 0.49,
        "oliver": 0.42,
        "stefan": 0.38,
    },
}


def demo_embedding(similarity: float) -> list[float]:
    return [similarity, (1 - similarity**2) ** 0.5, 0.0, 0.0]


def reset_and_seed(session: Session) -> None:
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    session.execute(delete(CallLog))
    session.execute(delete(OutreachAction))
    session.execute(delete(CandidateApproval))
    session.execute(delete(PipelineEvent))
    session.execute(delete(WorkflowStatus))
    session.execute(delete(JobCandidateVector))
    session.execute(delete(CandidateVector))
    session.execute(delete(Candidate))
    session.execute(delete(Job))

    for job_data in DEMO_JOBS:
        session.add(Job(**job_data))

    for data in DEMO_CANDIDATES:
        candidate_fields = {k: v for k, v in data.items() if k != "embedding"}
        session.add(Candidate(**candidate_fields))
        session.add(
            CandidateVector(
                candidate_id=data["id"],
                embedding=demo_embedding(data["fixed_similarity"]),
            )
        )
        for job_id, similarities in ROLE_SIMILARITIES.items():
            session.add(
                JobCandidateVector(
                    job_id=job_id,
                    candidate_id=data["id"],
                    embedding=demo_embedding(similarities[data["id"]]),
                )
            )

    session.commit()
    set_state(WorkflowState.seeded, session)
    set_active_job_id("demo-it-pm", session)

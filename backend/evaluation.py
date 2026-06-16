ROLE_EVALUATIONS = {
    "demo-it-pm": {
        "katharina": {
            "score": 91,
            "rationale": "Sehr hoher Fit durch PRINCE2, Energiebranche und mehrjährige Projektleitung.",
            "channel": "linkedin_inmail",
            "qualified": True,
            "risk_flags": [],
        },
        "daniel": {
            "score": 85,
            "rationale": "Hoher Fit durch SAFe, IT-Infrastruktur und Führungsnähe.",
            "channel": "linkedin_inmail",
            "qualified": True,
            "risk_flags": [],
        },
        "miriam": {
            "score": 83,
            "rationale": "Guter Fit durch PMP, Großprojekterfahrung und Stakeholder-Management. Für Voice Outreach priorisiert.",
            "channel": "voice_call",
            "qualified": True,
            "risk_flags": [],
        },
    },
    "demo-cloud-architect": {
        "daniel": {
            "score": 92,
            "rationale": "Sehr hoher Fit durch Infrastrukturführung, SAFe-Erfahrung und Nähe zu regulierten IT-Landschaften.",
            "channel": "linkedin_inmail",
            "qualified": True,
            "risk_flags": [],
        },
        "stefan": {
            "score": 78,
            "rationale": "Solide operative IT-Nähe für Cloud-Migration, aber Architektur- und Security-Tiefe bleiben unklar.",
            "channel": "outlook_email",
            "qualified": True,
            "risk_flags": ["architecture_depth_unclear"],
        },
        "katharina": {
            "score": 66,
            "rationale": "Starke Programmsteuerung, aber nur indirekte Cloud-Architektur-Nähe.",
            "channel": "linkedin_inmail",
            "qualified": False,
            "risk_flags": ["limited_cloud_architecture_fit"],
        },
        "miriam": {
            "score": 59,
            "rationale": "Gute Governance- und Stakeholder-Stärke, aber kaum belastbare Cloud- oder Plattformarchitektur-Signale.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["limited_cloud_architecture_fit"],
        },
        "oliver": {
            "score": 48,
            "rationale": "Allgemeines Projektmanagementprofil ohne Cloud-, Security- oder Architekturbezug.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["missing_cloud_depth"],
        },
        "petra": {
            "score": 37,
            "rationale": "Archivprofil liefert keine aktuellen Hinweise auf Cloud-Architektur oder regulierte Plattformmigration.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["profile_outdated"],
        },
    },
    "demo-data-engineer": {
        "miriam": {
            "score": 82,
            "rationale": "Guter Fit für datengetriebene Großprojekte und Stakeholder-Brücke zwischen Fachbereich und Umsetzung.",
            "channel": "voice_call",
            "qualified": True,
            "risk_flags": ["hands_on_engineering_unclear"],
        },
        "petra": {
            "score": 73,
            "rationale": "Archivprofil zeigt Datenprojekt-Nähe, ist aber veraltet und müsste vor Outreach validiert werden.",
            "channel": "outlook_email",
            "qualified": True,
            "risk_flags": ["profile_outdated"],
        },
        "daniel": {
            "score": 68,
            "rationale": "Technische Führungsnähe vorhanden, aber wenig direkte Data-Engineering-Signale.",
            "channel": "linkedin_inmail",
            "qualified": False,
            "risk_flags": ["limited_data_engineering_fit"],
        },
        "katharina": {
            "score": 51,
            "rationale": "Starke Projektleitung, aber keine ausreichenden Hands-on-Signale für Python, Pipelines oder Energiedatenplattformen.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["missing_data_engineering_depth"],
        },
        "oliver": {
            "score": 44,
            "rationale": "Methodisch anschlussfähig, aber ohne erkennbaren Bezug zu Datenplattformen, IoT oder Smart-Grid-Kontext.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["insufficient_role_fit"],
        },
        "stefan": {
            "score": 39,
            "rationale": "Operatives Profil ohne belastbare Data-Engineering- oder Pipeline-Erfahrung.",
            "channel": "none",
            "qualified": False,
            "risk_flags": ["missing_data_engineering_depth"],
        },
    },
}

CONTACT_PROFILES = {
    "katharina": {
        "available_channels": ["linkedin_inmail", "outlook_email"],
        "interaction_summary": [
            "LinkedIn Profil zuletzt vor 12 Tagen aktiv.",
            "Outlook: Demo Recruiting Event 2024 nachgefasst, keine Bewerbung.",
            "Workday: kein aktiver Bewerbungsprozess.",
        ],
        "has_workday_profile": False,
    },
    "daniel": {
        "available_channels": ["linkedin_inmail", "outlook_email", "voice_call"],
        "interaction_summary": [
            "LinkedIn: bestehender Kontakt zu Demo Tech Recruiter.",
            "Outlook: Austausch zu Infrastruktur-Rolle im Vorjahr.",
            "Telefonnummer aus früherem Screening vorhanden.",
        ],
        "phone_number": "+491000000000",
        "has_workday_profile": False,
    },
    "miriam": {
        "available_channels": ["voice_call", "outlook_email"],
        "interaction_summary": [
            "Workday: Initiativbewerbung am 14.02.2026 für Senior Projektmanagerin Transformation.",
            "Workday: CV und PMP-Zertifikat liegen als Demo-Anhänge vor.",
            "Outlook: automatische Eingangsbestätigung und Recruiter-Rückfrage zu Verfügbarkeit versendet.",
            "Telefonnummer für Demo-Recruiter Outreach freigegeben; letzter Kontakt blieb ohne Termin.",
        ],
        "phone_number": "+491000000000",
        "has_workday_profile": True,
    },
    "oliver": {
        "available_channels": ["outlook_email"],
        "interaction_summary": [
            "Outlook: CV aus Hiring Manager Weiterleitung.",
            "Workday: kein vollständiges Profil vorhanden.",
        ],
        "has_workday_profile": False,
    },
    "stefan": {
        "available_channels": ["linkedin_inmail", "outlook_email"],
        "interaction_summary": [
            "LinkedIn: Profil aus Talent Pool Import.",
            "Outlook: keine direkte Interaktion dokumentiert.",
        ],
        "has_workday_profile": False,
    },
    "petra": {
        "available_channels": ["outlook_email"],
        "interaction_summary": [
            "Workday: archivierte Bewerbung vom 03.11.2023 für Data Platform Analyst.",
            "Workday: CV aus 2023 vorhanden; Profil seit 26 Monaten nicht aktualisiert.",
            "Outlook: letzte Nachricht zur Datenplattform-Rolle offen; kein Follow-up dokumentiert.",
        ],
        "has_workday_profile": True,
    },
}


def _fallback(candidate) -> dict:
    return {
        "score": candidate.fixed_score,
        "rationale": candidate.rationale,
        "channel": candidate.channel,
        "qualified": candidate.qualified,
        "risk_flags": [] if candidate.qualified else ["insufficient_role_fit"],
    }


def contact_profile_for(candidate_id: str) -> dict:
    profile = CONTACT_PROFILES.get(
        candidate_id,
        {
            "available_channels": ["outlook_email"],
            "interaction_summary": ["Keine früheren Interaktionen im Demo-Datensatz."],
        },
    )
    has_workday_profile = profile.get("has_workday_profile", False)
    return {
        **profile,
        "phone_number": profile.get("phone_number"),
        "has_workday_profile": has_workday_profile,
        "workday_profile_url": f"/workday.html?candidate={candidate_id}"
        if has_workday_profile
        else None,
    }


def evaluate_candidates(candidates: list[dict], job_id: str = "demo-it-pm") -> list[dict]:
    evaluated: list[dict] = []
    for item in candidates:
        candidate = item["candidate"]
        role_eval = ROLE_EVALUATIONS.get(job_id, {}).get(candidate.id, _fallback(candidate))
        contact_profile = contact_profile_for(candidate.id)
        evaluated.append(
            {
                "id": candidate.id,
                "name": candidate.name,
                "source": candidate.source,
                "descriptor": candidate.descriptor,
                "score": role_eval["score"],
                "vector_similarity": round(item["vector_similarity"], 2),
                "rationale": role_eval["rationale"],
                "channel": role_eval["channel"],
                "available_channels": contact_profile["available_channels"],
                "interaction_summary": contact_profile["interaction_summary"],
                "phone_number": contact_profile["phone_number"],
                "has_workday_profile": contact_profile["has_workday_profile"],
                "workday_profile_url": contact_profile["workday_profile_url"],
                "qualified": role_eval["qualified"],
                "risk_flags": role_eval["risk_flags"],
            }
        )
    return evaluated


def outreach_channel_for(
    job_id: str, candidate_id: str, fallback_channel: str = "linkedin_inmail"
) -> str:
    return ROLE_EVALUATIONS.get(job_id, {}).get(candidate_id, {}).get("channel", fallback_channel)

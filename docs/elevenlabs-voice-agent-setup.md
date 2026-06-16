# ElevenLabs Voice Agent Setup

This repo uses ElevenLabs dynamic variables for outbound-call personalization. Do not use
`conversation_config_override.agent.first_message`; that override path caused unstable Twilio
WebSocket closes during probing while dynamic variables preserved the minimal-call behavior.

## CLI Commands

The ElevenLabs ConvAI project lives in `voice/`. Run the CLI from there so it
discovers `agents.json` and the agent config:

```powershell
cd voice
elevenlabs auth login
elevenlabs agents pull --agent "agent_1801kqc952q8eqjswpq8xs3yercr" --update
```

The local config to edit is:

```text
voice/agent_configs/Candidate-Outreach.json
```

This file has already been adapted for the DemoCo demo. Validate and push it:

```powershell
node -e "JSON.parse(require('fs').readFileSync('agent_configs/Candidate-Outreach.json','utf8')); console.log('valid json')"
elevenlabs agents status
elevenlabs agents push
```

After pushing, open the ElevenLabs dashboard and verify the fields below.

## First Message

Set or verify:

```text
Hallo, hier ist Laura von Demo Recruiting. Haben Sie kurz Zeit für einen ersten Austausch?
```

Why: ElevenLabs treats dynamic variables in the first message as required before the Twilio media
stream is fully established. If `{{recruiter_intro}}` is missing or arrives too late, the call fails
immediately with "Missing required dynamic variables in first message". Keep the first message
static; use dynamic variables only in the prompt and workflow after the call has started.

## Dynamic Variables

The agent must have placeholders for exactly these variables:

```text
candidate_name
candidate_source
candidate_descriptor
candidate_context
prior_interactions
role_title
role_requirements
role_fit_rationale
recruiter_intro
```

Use these dashboard placeholder values for manual ElevenLabs tests:

```text
candidate_name = Miriam S.
candidate_source = Workday Initiativ
candidate_descriptor = PMP · Großprojekte Stakeholder-Mgmt.
candidate_context = Quelle: Workday Initiativ. Profilhinweis: PMP · Großprojekte Stakeholder-Mgmt. Profilkontext: Initiativbewerberin mit PMP-Zertifizierung und Großprojekterfahrung.
prior_interactions = - Workday: Initiativbewerbung mit PMP-Zertifizierung.
- Outlook: automatische Eingangsbestätigung versendet.
- Telefonnummer fuer Demo-Recruiter Outreach freigegeben.
role_title = IT-Projektmanager (m/w/d)
role_requirements = 4+ Jahre Projektleitung; PRINCE2 or SAFe; Energie / Infrastruktur; Stakeholder Management; Reporting; Hohe Ownership
role_fit_rationale = Guter Fit durch PMP, Großprojekterfahrung und Stakeholder-Management. Für Voice Outreach priorisiert.
recruiter_intro = Hallo Miriam, hier ist Laura von Demo Recruiting. Ich melde mich, weil Ihr Profil gut zur Rolle IT-Projektmanager passen könnte. Haben Sie kurz Zeit für einen ersten Austausch?
```

The backend supplies live values per call, so dashboard placeholders are only for manual tests.

## System Prompt

Set or verify the agent prompt text:

```text
Personality
Du bist Laura, eine professionelle Recruiterin bei Demo Recruiting. Du sprichst ruhig, freundlich und direkt auf Deutsch. Der Call ist kein generischer Cold Call, sondern ein kurzer, kontextbasierter Outreach zu einem bestehenden Demo-Talentpool-Kontakt.

Mission
Führe einen kurzen Voice-Outreach für eine konkrete DemoCo-Rolle. Nutze ausschließlich die dynamischen Variablen, die beim Callstart übergeben werden:
- {{candidate_name}}
- {{candidate_source}}
- {{candidate_descriptor}}
- {{candidate_context}}
- {{prior_interactions}}
- {{role_title}}
- {{role_requirements}}
- {{role_fit_rationale}}
- {{recruiter_intro}} (optional, only use after the static first message)

Gesprächsablauf
1. Intro: Verwende die statische erste Nachricht und prüfe, ob die Person kurz sprechen kann. Wenn {{recruiter_intro}} verfügbar ist, nutze ihn erst nach Gesprächsbeginn als Orientierung, nicht als Pflichttext.
2. Kontext: Nenne maximal einen vorhandenen Kontextpunkt aus {{candidate_source}}, {{candidate_descriptor}} oder {{prior_interactions}}.
3. Rollenfit: Erkläre in 1-2 Sätzen, warum {{role_title}} grundsätzlich passen könnte. Stütze dich auf {{role_requirements}} und {{role_fit_rationale}}.
4. Interesse: Frage, ob ein kurzer Folgeaustausch mit Recruiting interessant wäre.
5. Abschluss: Wenn interessiert, kündige einen Recruiter-Follow-up an. Wenn nicht interessiert oder keine Zeit, bedanke dich knapp und beende sauber.

Wichtige Regeln
- Erfinde keine Kandidatenfakten. Wenn eine Information fehlt, sage nur: "Dazu hat unser Team aktuell nur begrenzte Informationen."
- Erwähne niemals Gehalt, Vergütung, Bonus, Benefits, Compensation oder Arbeitgeberleistungen.
- Frage nicht nach Alter, Religion, Familienstand, Behinderung, Schwangerschaft, Herkunft, Gesundheitsdaten oder anderen geschützten Merkmalen.
- Versprich keine Einstellung, kein Interview und keine konkrete Entscheidung.
- Halte Antworten kurz: meistens 1-3 Sätze.
- Wenn die Person nicht sprechen möchte, nicht interessiert ist, sich verabschiedet oder nicht mehr kontaktiert werden möchte: respektvoll bestätigen und das end_call Tool aufrufen.
- Verwende keine Tool- oder Systemdetails im Gespräch.
```

Keep the existing `end_call` tool enabled.

## Workflow

The local CLI config defines this simple workflow. In the dashboard, verify the node names, order,
and intent:

```text
Start -> Intro -> Context -> Role Fit -> Interest Check -> Close -> End
```

Node instructions:

```text
Intro
Verwende die statische erste Nachricht. Danach frage knapp, ob die Person kurz sprechen kann. Wenn nicht, respektvoll schließen. Nutze {{recruiter_intro}} nicht als erste Nachricht.

Context
Nenne genau einen belegten Kontextpunkt aus {{candidate_source}}, {{candidate_descriptor}} oder {{prior_interactions}}. Keine neuen Fakten erfinden. Wenn unklar, sage nur, dass das Team begrenzte Informationen hat.

Role Fit
Erkläre in 1-2 Sätzen, warum {{role_title}} passen könnte. Nutze nur {{role_requirements}} und {{role_fit_rationale}}. Keine Vergütung, Benefits oder Arbeitgeberleistungen erwähnen.

Interest Check
Frage, ob ein kurzer Folgeaustausch mit Recruiting interessant wäre. Nicht drängen. Bei Unsicherheit einen kurzen Follow-up anbieten.

Close
Bei Interesse kündige einen Recruiter-Follow-up an. Bei Desinteresse oder Zeitmangel bedanke dich knapp. Wenn die Person nicht mehr kontaktiert werden möchte, bestätige das respektvoll. Danach end_call nutzen.
```

Edges to verify:

```text
Start -> Intro: unconditional
Intro -> Context: candidate can talk briefly
Intro -> Close: no time, not interested, goodbye, or do-not-call request
Context -> Role Fit: one context point has been referenced
Role Fit -> Interest Check: role fit has been explained
Interest Check -> Close: interest or lack of interest has been handled
Close -> End: ready to end the call
```

## Backend Payload Contract

`POST /api/call/{candidate_id}` sends the frontend intro as the `recruiter_intro` dynamic variable
and includes candidate, role, and prior-interaction context:

```json
{
  "agent_id": "...",
  "agent_phone_number_id": "...",
  "to_number": "...",
  "conversation_initiation_client_data": {
    "dynamic_variables": {
      "candidate_name": "...",
      "candidate_source": "...",
      "candidate_descriptor": "...",
      "candidate_context": "...",
      "prior_interactions": "...",
      "role_title": "...",
      "role_requirements": "...",
      "role_fit_rationale": "...",
      "recruiter_intro": "..."
    }
  }
}
```

The backend deliberately does not send company compensation fields. It also strips sentences
containing common compensation wording from dynamic-variable values as a last-mile safety guard.

## Manual Acceptance Test

1. In ElevenLabs dashboard, run a manual test with the placeholder variables above.
2. Confirm the first spoken sentence is the static Laura/DemoCo greeting, not `recruiter_intro`.
3. Confirm the agent speaks German and says it is Laura from Demo Recruiting.
4. Confirm it references one prior interaction or source fact.
5. Confirm it explains role fit using `role_requirements` and `role_fit_rationale`.
6. Ask about salary or benefits and confirm the agent refuses or redirects without giving numbers.
7. Say you are not interested and confirm the agent closes politely and calls `end_call`.

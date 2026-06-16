// @ts-nocheck
import React, { useCallback, useEffect, useMemo, useState } from "react";

// ---------- Tokens ----------
const T = {
  bg: "#071014",
  bgSoft: "#0B1117",
  surface: "#101820",
  surface2: "#121A22",
  surface3: "#172230",
  border: "rgba(255,255,255,0.06)",
  borderStrong: "rgba(255,255,255,0.10)",
  text: "#F7F4EA",
  textDim: "#AEB7B3",
  textFaint: "#6B7A7E",
  yellow: "#FFD700",
  yellowSoft: "rgba(255,215,0,0.14)",
  amber: "#E8B43A",
  amberSoft: "rgba(232,180,58,0.10)",
  green: "#7FB283",
  red: "#D97468",
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const TOP_CANDIDATE_IDS = ["katharina", "daniel", "miriam"];
const DEFAULT_PHONE_NUMBER = "+491000000000";

const channelLabel = (channel) => {
  const labels = {
    linkedin_inmail: "LinkedIn InMail",
    outlook_email: "Outlook Email",
    voice_call: "Voice Call",
    phone: "Voice Call",
    workday: "Workday",
    none: "-",
  };
  return labels[channel] || channel;
};

const riskFlagLabel = (flag) => {
  const labels = {
    architecture_depth_unclear: "Architektur-Tiefe unklar",
    limited_cloud_architecture_fit: "Cloud-Architektur-Fit begrenzt",
    missing_cloud_depth: "Cloud-Tiefe fehlt",
    profile_outdated: "Profil veraltet",
    hands_on_engineering_unclear: "Hands-on-Engineering unklar",
    limited_data_engineering_fit: "Data-Engineering-Fit begrenzt",
    missing_data_engineering_depth: "Data-Engineering-Tiefe fehlt",
    insufficient_role_fit: "Rollen-Fit unzureichend",
  };
  if (labels[flag]) return labels[flag];
  // Fallback: humanize an unknown snake_case key instead of showing it raw.
  return flag.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
};

const contactChannels = (channels = []) =>
  [...new Set(channels.map(channelLabel).filter((channel) => channel !== "-" && channel !== "Workday"))];

const draftKey = (candidateId, channel) => `${candidateId}:${channel}`;

const defaultPhoneForCandidate = (candidate) => candidate?.phone_number || DEFAULT_PHONE_NUMBER;

const defaultOutreachDraft = (candidate, channel) => {
  if (!candidate) return "";

  if (channel === "Outlook Email") {
    return `Betreff: Austausch zur Rolle bei DemoCo\n\nHallo ${candidate.name},\n\nIhr Profil passt sehr gut zu einer aktuellen Rolle bei DemoCo. Besonders relevant sind aus unserer Sicht ${candidate.descriptor}.\n\nHätten Sie in den nächsten Tagen 20 Minuten Zeit für einen ersten Austausch?\n\nViele Grüße\nDemo Recruiting`;
  }

  if (channel === "Voice Call") {
    return `Hallo ${candidate.name}, hier ist Demo Recruiting. Ich melde mich, weil Ihr Profil sehr gut zu einer aktuellen Rolle bei DemoCo passt. Ich würde gerne kurz besprechen, ob ein erster Austausch für Sie interessant ist.`;
  }

  return `Hallo ${candidate.name}, Ihr Profil ist uns im Demo Talentpool aufgefallen. ${candidate.descriptor} passt sehr gut zu einer aktuellen Rolle. Hätten Sie Interesse an einem kurzen Austausch?`;
};

const toUiCandidate = (candidate, index) => ({
  ...candidate,
  rank: index + 1,
  score: candidate.score > 1 ? candidate.score / 100 : candidate.score,
  channel: channelLabel(candidate.channel),
  available_channels: contactChannels(candidate.available_channels || [candidate.channel]),
  interaction_summary: candidate.interaction_summary || [],
  phone_number: candidate.phone_number || null,
  has_workday_profile: Boolean(candidate.has_workday_profile),
});

const toUiAction = (action) => ({
  ...action,
  channel: channelLabel(action.channel),
});

const approvalsToMap = (approvals = []) =>
  approvals.reduce((acc, approval) => {
    acc[approval.candidate_id] = approval.decision;
    return acc;
  }, {});

const stepsForState = (workflowState) => {
  if (workflowState === "idle" || workflowState === "seeded") return [];
  if (workflowState === "analyzing") return ["anf", "vec"];
  if (workflowState === "paused_for_recruiter_approval") return ["anf", "vec", "eval", "konflikt"];
  if (workflowState === "approved" || workflowState === "outreach_ready") {
    return ["anf", "vec", "eval", "konflikt", "freigabe", "outreach"];
  }
  if (workflowState === "call_in_progress" || workflowState === "call_completed") {
    return ["anf", "vec", "eval", "konflikt", "freigabe", "outreach", "call"];
  }
  return [];
};

const apiRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { accept: "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `API request failed: ${path}`);
  }
  return payload;
};

// ---------- Position fixtures ----------
const POSITIONS = [
  {
    id: "demo-it-pm",
    title: "IT-Projektmanager (m/w/d)",
    company: "Demo Energy AG",
    tags: ["PRINCE2 / SAFe", "4+ Jahre", "Energie", "Stakeholder-Mgmt.", "Hohe Ownership"],
    description: "Steuerung strategischer IT-Programme im regulierten Energieumfeld. Verantwortung über Budget, Stakeholder und Lieferketten.",
  },
  {
    id: "demo-cloud-architect",
    title: "Cloud Architect (m/w/d)",
    company: "Demo Energy AG · IT Infrastructure",
    tags: ["AWS / Azure", "Kubernetes", "Energie", "Security Clearance", "6+ Jahre"],
    description: "Design und Migration kritischer Energie-Workloads in eine hybride Cloud. Tiefe Erfahrung in regulierten Umgebungen erforderlich.",
  },
  {
    id: "demo-data-engineer",
    title: "Data Engineer Smart Grid (m/w/d)",
    company: "Demo Energy AG · Grid Operations",
    tags: ["Python", "dbt / Airflow", "IoT", "Energiedaten", "3+ Jahre"],
    description: "Aufbau einer Datenplattform für Netzbetrieb und Verbrauchsanalysen. Schnittstelle zwischen Engineering, Netzleittechnik und BI.",
  },
];

// ---------- Fixtures ----------
const FIXTURE_CANDIDATES = [
  {
    id: "c1",
    rank: 1,
    name: "Katharina B.",
    source: "LinkedIn",
    descriptor: "PRINCE2 · 7 Jahre Energiebranche",
    score: 0.91,
    vector_similarity: 0.88,
    rationale:
      "Starke fachliche Übereinstimmung. PRINCE2-Zertifizierung und langjährige Erfahrung in regulierten Energieprojekten. Stakeholder-Management auf Vorstandsebene dokumentiert.",
    channel: "LinkedIn InMail",
    qualified: true,
    risk_flags: [],
  },
  {
    id: "c2",
    rank: 2,
    name: "Daniel W.",
    source: "LinkedIn",
    descriptor: "SAFe Agilist · IT-Leiter Infrastruktur",
    score: 0.85,
    vector_similarity: 0.82,
    rationale:
      "Hybrid aus SAFe-Methodik und operativer IT-Verantwortung. Profil deckt Infrastruktur-Migration in regulierten Branchen ab. Hohe Ownership-Signale.",
    channel: "LinkedIn InMail",
    qualified: true,
    risk_flags: [],
  },
  {
    id: "c3",
    rank: 3,
    name: "Miriam S.",
    source: "Workday Initiativ",
    descriptor: "PMP · Großprojekte Stakeholder-Mgmt.",
    score: 0.83,
    vector_similarity: 0.80,
    rationale:
      "Initiativbewerbung mit hoher semantischer Übereinstimmung. PMP, Großprojekt-Erfahrung im öffentlichen Sektor, ausgeprägtes Stakeholder-Management. Bevorzugt persönlichen Erstkontakt.",
    channel: "Voice Call",
    qualified: true,
    risk_flags: ["Strategische Personalplanung"],
  },
  {
    id: "c4",
    rank: 4,
    name: "Oliver T.",
    source: "Outlook",
    descriptor: "Kein Branchenbezug",
    score: 0.62,
    vector_similarity: 0.58,
    rationale:
      "PM-Profil ohne Energiekontext. Methodisch solide, fachlich nicht spezifisch. Kein priorisierter Outreach.",
    channel: "—",
    qualified: false,
    risk_flags: ["Branchenmismatch"],
  },
  {
    id: "c5",
    rank: 5,
    name: "Stefan M.",
    source: "LinkedIn",
    descriptor: "Kein IT-Hintergrund",
    score: 0.54,
    vector_similarity: 0.49,
    rationale:
      "PM-Methoden vorhanden, aber keine IT-Projektverantwortung. Nicht qualifiziert für die Rolle.",
    channel: "—",
    qualified: false,
    risk_flags: ["Fachprofil unpassend"],
  },
  {
    id: "c6",
    rank: 6,
    name: "Petra F.",
    source: "Workday Archiv",
    descriptor: "Veraltetes Profil",
    score: 0.46,
    vector_similarity: 0.44,
    rationale:
      "Profil seit 26 Monaten nicht aktualisiert. Letzter Stand: Junior-PM. Keine aktuelle Eignung.",
    channel: "—",
    qualified: false,
    risk_flags: ["Datenstand veraltet"],
  },
];

const AUDIT_STEPS = [
  { id: "anf", label: "Anforderungsanalyse" },
  { id: "vec", label: "Talentpool-Suche" },
  { id: "eval", label: "Evaluation API" },
  { id: "konflikt", label: "Konflikt-Check" },
  { id: "freigabe", label: "Recruiter-Freigabe" },
  { id: "outreach", label: "Outreach erstellt" },
  { id: "call", label: "Voice Call gestartet" },
];

// ---------- Tiny primitives ----------
const Dot = ({ color = T.green, size = 6 }) => (
  <span
    style={{
      width: size,
      height: size,
      borderRadius: 999,
      background: color,
      display: "inline-block",
      boxShadow: `0 0 0 3px ${color}22`,
    }}
  />
);

const StatusPill = ({ tone = "neutral", children, dot = true }) => {
  const map = {
    ok: { fg: T.green, bg: "rgba(127,178,131,0.10)", bd: "rgba(127,178,131,0.25)" },
    warn: { fg: T.amber, bg: T.amberSoft, bd: "rgba(232,180,58,0.30)" },
    err: { fg: T.red, bg: "rgba(217,116,104,0.10)", bd: "rgba(217,116,104,0.30)" },
    neutral: { fg: T.textDim, bg: "rgba(255,255,255,0.04)", bd: T.borderStrong },
    accent: { fg: T.yellow, bg: T.yellowSoft, bd: "rgba(255,215,0,0.28)" },
  };
  const c = map[tone];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "5px 10px",
        borderRadius: 999,
        background: c.bg,
        border: `1px solid ${c.bd}`,
        color: c.fg,
        fontSize: 12,
        letterSpacing: 0.2,
        fontWeight: 500,
        whiteSpace: "nowrap",
      }}
    >
      {dot && <Dot color={c.fg} />}
      {children}
    </span>
  );
};

const Card = ({ children, style, glow = false, padding = 24 }) => (
  <div
    style={{
      background: T.surface,
      border: `1px solid ${T.border}`,
      borderRadius: 16,
      padding,
      position: "relative",
      overflow: "hidden",
      boxShadow: "0 1px 0 rgba(255,255,255,0.02) inset, 0 20px 40px -30px rgba(0,0,0,0.6)",
      ...style,
    }}
  >
    {glow && (
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: -1,
          pointerEvents: "none",
          background:
            "radial-gradient(420px 220px at 100% 0%, rgba(255,215,0,0.08), transparent 60%)",
        }}
      />
    )}
    <div style={{ position: "relative" }}>{children}</div>
  </div>
);

// ---------- Top Bar ----------
const PageTab = ({ active, disabled, onClick, children, hint }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    title={hint}
    style={{
      padding: "8px 14px",
      borderRadius: 10,
      border: `1px solid ${active ? "rgba(255,215,0,0.32)" : T.border}`,
      background: active ? T.yellowSoft : "transparent",
      color: active ? T.text : disabled ? T.textFaint : T.textDim,
      fontSize: 12.5,
      fontWeight: 600,
      letterSpacing: 0.2,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.55 : 1,
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
    }}
  >
    {children}
  </button>
);

const TopBar = ({ backendOk, voiceOk, page, setPage, position, cockpitUnlocked }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "16px 28px",
      borderBottom: `1px solid ${T.border}`,
      background: "rgba(7,16,20,0.7)",
      backdropFilter: "blur(8px)",
      position: "sticky",
      top: 0,
      zIndex: 10,
      gap: 24,
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 18, minWidth: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
        <div
          style={{
            fontFamily:
              "ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', Helvetica, Arial",
            fontWeight: 800,
            fontSize: 22,
            letterSpacing: 1.2,
            color: T.yellow,
            textShadow: "0 0 24px rgba(255,215,0,0.25)",
            lineHeight: 1,
          }}
        >
          DemoCo
        </div>
        <div style={{ fontSize: 10.5, color: T.textFaint, fontStyle: "italic", letterSpacing: 0.2 }}>
          Wir gestalten Zukunft.
        </div>
      </div>
      <div style={{ width: 1, height: 32, background: T.borderStrong }} />
      <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.2, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: T.text }}>
          Talent Scout
        </div>
        <div style={{ fontSize: 12, color: T.textDim, marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 320 }}>
          {position ? `DemoCo · ${position.title}` : "DemoCo"}
        </div>
      </div>
      <div style={{ display: "flex", gap: 6, marginLeft: 12 }}>
        <PageTab active={page === "briefing"} onClick={() => setPage("briefing")}>Briefing</PageTab>
        <PageTab active={page === "cockpit"} disabled={!cockpitUnlocked} onClick={() => cockpitUnlocked && setPage("cockpit")} hint={!cockpitUnlocked ? "Sourcing Run starten, um den Cockpit zu öffnen" : undefined}>
          Cockpit
        </PageTab>
      </div>
    </div>
    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
      <StatusPill tone={backendOk ? "ok" : "err"}>
        {backendOk ? "Backend verbunden" : "Backend nicht erreichbar"}
      </StatusPill>
      <StatusPill tone={voiceOk ? "ok" : "warn"}>
        {voiceOk ? "Voice bereit" : "Live Voice nicht konfiguriert"}
      </StatusPill>
      <StatusPill tone="neutral" dot={false}>
        Mock-Up Daten
      </StatusPill>
    </div>
  </div>
);

// ---------- Panel 1: Job Brief & Run Control ----------
const Tag = ({ children }) => (
  <span
    style={{
      display: "inline-flex",
      padding: "6px 10px",
      borderRadius: 8,
      background: "rgba(255,255,255,0.03)",
      border: `1px solid ${T.border}`,
      color: T.text,
      fontSize: 12.5,
      fontWeight: 500,
    }}
  >
    {children}
  </span>
);

// Briefing page: a centered, sleek single-card view of the position.
// Includes a position picker (alternatives) and inline edit for title/company/tags.
const PositionPicker = ({ positions, currentId, onSelect }) => (
  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
    {positions.map((p) => {
      const active = p.id === currentId;
      return (
        <button
          key={p.id}
          onClick={() => onSelect(p.id)}
          style={{
            padding: "8px 12px",
            borderRadius: 999,
            border: `1px solid ${active ? "rgba(255,215,0,0.32)" : T.border}`,
            background: active ? T.yellowSoft : "rgba(255,255,255,0.02)",
            color: active ? T.text : T.textDim,
            fontSize: 12.5,
            fontWeight: 500,
            cursor: "pointer",
            whiteSpace: "nowrap",
          }}
        >
          {p.title}
        </button>
      );
    })}
  </div>
);

const InlineEditable = ({ value, onChange, fontSize = 14, fontWeight = 500, color = T.text, placeholder = "" }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  if (editing) {
    return (
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => { onChange(draft); setEditing(false); }}
        onKeyDown={(e) => {
          if (e.key === "Enter") { onChange(draft); setEditing(false); }
          if (e.key === "Escape") { setDraft(value); setEditing(false); }
        }}
        placeholder={placeholder}
        style={{
          fontSize, fontWeight, color,
          background: "rgba(255,215,0,0.06)",
          border: "1px solid rgba(255,215,0,0.32)",
          borderRadius: 8,
          padding: "4px 8px",
          outline: "none",
          width: "100%",
          fontFamily: "inherit",
          letterSpacing: -0.3,
        }}
      />
    );
  }
  return (
    <span
      onClick={() => setEditing(true)}
      style={{
        fontSize, fontWeight, color,
        cursor: "text",
        borderBottom: "1px dashed transparent",
        transition: "border-color 150ms",
        display: "inline-block",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderBottomColor = "rgba(255,215,0,0.3)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderBottomColor = "transparent")}
    >
      {value || <span style={{ color: T.textFaint }}>{placeholder}</span>}
    </span>
  );
};

const EditableTagList = ({ tags, onChange }) => {
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState("");
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
      {tags.map((t, i) => (
        <span
          key={i}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "6px 10px",
            borderRadius: 8,
            background: "rgba(255,255,255,0.03)",
            border: `1px solid ${T.border}`,
            color: T.text,
            fontSize: 12.5,
            fontWeight: 500,
          }}
        >
          {t}
          <button
            onClick={() => onChange(tags.filter((_, j) => j !== i))}
            style={{
              background: "none",
              border: "none",
              color: T.textFaint,
              cursor: "pointer",
              padding: 0,
              fontSize: 14,
              lineHeight: 1,
            }}
            aria-label="Tag entfernen"
          >×</button>
        </span>
      ))}
      {adding ? (
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={() => {
            if (draft.trim()) onChange([...tags, draft.trim()]);
            setDraft(""); setAdding(false);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              if (draft.trim()) onChange([...tags, draft.trim()]);
              setDraft(""); setAdding(false);
            }
            if (e.key === "Escape") { setDraft(""); setAdding(false); }
          }}
          placeholder="Skill hinzufügen…"
          style={{
            padding: "6px 10px", borderRadius: 8,
            background: "rgba(255,215,0,0.06)",
            border: "1px solid rgba(255,215,0,0.32)",
            color: T.text, fontSize: 12.5, outline: "none",
            fontFamily: "inherit",
          }}
        />
      ) : (
        <button
          onClick={() => setAdding(true)}
          style={{
            padding: "6px 10px", borderRadius: 8,
            background: "transparent",
            border: `1px dashed ${T.borderStrong}`,
            color: T.textFaint, fontSize: 12.5, cursor: "pointer",
          }}
        >+ Skill</button>
      )}
    </div>
  );
};

const BriefingPage = ({ position, positions, onPickPosition, onUpdatePosition, onStart, onReset, state }) => {
  const running = state === "analyzing";
  const idle = state === "idle" || state === "seeded";
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "48px 28px",
        position: "relative",
        zIndex: 1,
      }}
    >
      <div style={{ width: "100%", maxWidth: 720, display: "flex", flexDirection: "column", gap: 18 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ fontSize: 11, letterSpacing: 1.8, textTransform: "uppercase", color: T.textFaint }}>
            Briefing · Position auswählen
          </div>
          <span style={{ fontSize: 11.5, color: T.textFaint }}>
            {positions.length} Demo-Positionen
          </span>
        </div>

        <PositionPicker positions={positions} currentId={position.id} onSelect={onPickPosition} />

        <Card glow padding={32}>
          <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
            <div>
              <div style={{ fontSize: 11, letterSpacing: 1.6, color: T.textFaint, textTransform: "uppercase", marginBottom: 10 }}>
                Position
              </div>
              <div style={{ fontSize: 30, fontWeight: 600, color: T.text, letterSpacing: -0.4, lineHeight: 1.15 }}>
                <InlineEditable
                  value={position.title}
                  onChange={(v) => onUpdatePosition({ title: v })}
                  fontSize={30}
                  fontWeight={600}
                  color={T.text}
                  placeholder="Positionstitel"
                />
              </div>
              <div style={{ fontSize: 14, color: T.textDim, marginTop: 8 }}>
                <InlineEditable
                  value={position.company}
                  onChange={(v) => onUpdatePosition({ company: v })}
                  fontSize={14}
                  fontWeight={400}
                  color={T.textDim}
                  placeholder="Unternehmen"
                />
              </div>
            </div>

            <div style={{ fontSize: 13.5, color: T.text, lineHeight: 1.6 }}>
              <InlineEditable
                value={position.description}
                onChange={(v) => onUpdatePosition({ description: v })}
                fontSize={13.5}
                fontWeight={400}
                color={T.text}
                placeholder="Kurzbeschreibung"
              />
            </div>

            <div>
              <div style={{ fontSize: 11, letterSpacing: 1.4, color: T.textFaint, textTransform: "uppercase", marginBottom: 10 }}>
                Anforderungen
              </div>
              <EditableTagList
                tags={position.tags}
                onChange={(tags) => onUpdatePosition({ tags })}
              />
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                borderRadius: 10,
                border: `1px dashed ${T.borderStrong}`,
                color: T.textDim,
                fontSize: 12.5,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              }}
            >
              <Dot color={T.textFaint} />
              Mock-up Talentpool in Postgres
            </div>

            <div
              style={{
                padding: "12px 14px",
                borderRadius: 10,
                background: "linear-gradient(180deg, rgba(255,215,0,0.06), rgba(255,215,0,0.02))",
                border: "1px solid rgba(255,215,0,0.14)",
                color: T.text,
                fontSize: 13.5,
                fontStyle: "italic",
                letterSpacing: 0.1,
                textAlign: "center",
              }}
            >
              „Wir gestalten Zukunft — auch im Recruiting."
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
              <button
                onClick={onStart}
                disabled={running || !idle}
                style={{
                  flex: 1,
                  position: "relative",
                  padding: "14px 18px",
                  borderRadius: 12,
                  border: "1px solid rgba(255,215,0,0.4)",
                  background: idle
                    ? "linear-gradient(180deg, #FFE34A, #F2C400)"
                    : "rgba(255,215,0,0.10)",
                  color: idle ? "#1A1300" : T.textDim,
                  fontWeight: 700,
                  fontSize: 14.5,
                  letterSpacing: 0.2,
                  cursor: running || !idle ? "default" : "pointer",
                  boxShadow: idle ? "0 0 0 6px rgba(255,215,0,0.08), 0 14px 30px -12px rgba(255,215,0,0.35)" : "none",
                  transition: "transform 120ms ease",
                }}
                onMouseDown={(e) => idle && (e.currentTarget.style.transform = "translateY(1px)")}
                onMouseUp={(e) => (e.currentTarget.style.transform = "translateY(0)")}
              >
                {running ? "Analyse läuft…" : idle ? "Sourcing Run starten" : "Run aktiv"}
              </button>
              <button
                onClick={onReset}
                style={{
                  padding: "12px 16px",
                  borderRadius: 12,
                  border: `1px solid ${T.borderStrong}`,
                  background: "transparent",
                  color: T.textDim,
                  fontWeight: 500,
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                Demo zurücksetzen
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

// ---------- Panel 2: Shortlist ----------
const ScoreBar = ({ value, dim = false }) => {
  const pct = Math.round(value * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 130 }}>
      <div
        style={{
          flex: 1,
          height: 6,
          borderRadius: 999,
          background: "rgba(255,255,255,0.06)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: dim
              ? "rgba(174,183,179,0.45)"
              : "linear-gradient(90deg, #F2C400, #FFE34A)",
            boxShadow: dim ? "none" : "0 0 12px rgba(255,215,0,0.35)",
            transition: "width 600ms cubic-bezier(.2,.7,.2,1)",
          }}
        />
      </div>
      <div
        style={{
          fontVariantNumeric: "tabular-nums",
          fontSize: 13,
          fontWeight: 600,
          color: dim ? T.textDim : T.text,
          minWidth: 38,
          textAlign: "right",
        }}
      >
        {pct}%
      </div>
    </div>
  );
};

const ChannelBadge = ({ channel }) => {
  if (channel === "Voice Call") {
    return <StatusPill tone="accent" dot={false}>● Voice Call</StatusPill>;
  }
  if (channel === "Outlook Email") {
    return <StatusPill tone="warn" dot={false}>Outlook</StatusPill>;
  }
  if (channel === "Workday") {
    return <StatusPill tone="neutral" dot={false}>Workday</StatusPill>;
  }
  if (channel === "—") {
    return (
      <span style={{ color: T.textFaint, fontSize: 12 }}>—</span>
    );
  }
  return (
    <span
      style={{
        fontSize: 12,
        color: T.textDim,
        padding: "4px 8px",
        borderRadius: 6,
        border: `1px solid ${T.border}`,
        background: "rgba(255,255,255,0.02)",
      }}
    >
      {channel}
    </span>
  );
};

const ApprovalBadge = ({ status }) => {
  if (status === "approved") {
    return <StatusPill tone="ok" dot={false}>✓ Freigegeben</StatusPill>;
  }
  if (status === "declined") {
    return <StatusPill tone="neutral" dot={false}>– Abgelehnt</StatusPill>;
  }
  if (status === "pending") {
    return <StatusPill tone="warn">Freigabe offen</StatusPill>;
  }
  return null;
};

const CandidateRow = ({ c, selected, onClick, dim, delay, approvalStatus, channel }) => {
  return (
    <div
      onClick={onClick}
      style={{
        display: "grid",
        gridTemplateColumns: "28px 1.4fr 0.9fr 1.1fr 0.9fr 0.8fr",
        alignItems: "center",
        gap: 14,
        padding: "14px 16px",
        borderRadius: 12,
        cursor: "pointer",
        background: selected
          ? "linear-gradient(180deg, rgba(255,215,0,0.07), rgba(255,215,0,0.02))"
          : "transparent",
        border: selected
          ? "1px solid rgba(255,215,0,0.32)"
          : `1px solid transparent`,
        opacity: dim ? 0.55 : 1,
        transition: "background 200ms ease, border-color 200ms ease, opacity 200ms ease",
        animation: `fadeUp 500ms ${delay}ms cubic-bezier(.2,.7,.2,1) backwards`,
      }}
      onMouseEnter={(e) => {
        if (!selected) e.currentTarget.style.background = "rgba(255,255,255,0.025)";
      }}
      onMouseLeave={(e) => {
        if (!selected) e.currentTarget.style.background = "transparent";
      }}
    >
      <div
        style={{
          fontVariantNumeric: "tabular-nums",
          fontSize: 13,
          color: dim ? T.textFaint : T.textDim,
          fontWeight: 500,
        }}
      >
        {String(c.rank).padStart(2, "0")}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <div style={{ fontSize: 14.5, fontWeight: 600, color: dim ? T.textDim : T.text }}>
          {c.name}
        </div>
        <div style={{ fontSize: 12, color: T.textFaint }}>{c.descriptor}</div>
      </div>
      <div style={{ fontSize: 12.5, color: T.textDim }}>{c.source}</div>
      <ScoreBar value={c.score} dim={dim} />
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <ChannelBadge channel={channel || c.channel} />
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <ApprovalBadge status={approvalStatus} />
      </div>
    </div>
  );
};

const ShortlistPanel = ({ state, candidates, selectedId, onSelect, approvals, selectedChannels }) => {
  const empty = state === "idle" || state === "analyzing";
  const showApprovalCol = state === "paused_for_recruiter_approval" || state === "outreach_ready" || state === "call_in_progress" || state === "call_completed";
  return (
    <Card padding={20} style={{ height: "100%" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "4px 6px 18px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: T.text, letterSpacing: -0.2 }}>Shortlist</div>
          <div style={{ fontSize: 12.5, color: T.textDim }}>
            {empty ? "—" : `${candidates.length} Profile geprüft`}
          </div>
        </div>
        {state === "analyzing" && (
          <StatusPill tone="accent">Analysiere…</StatusPill>
        )}
        {state === "paused_for_recruiter_approval" && (
          <StatusPill tone="warn">Einzelfreigabe je Kandidat</StatusPill>
        )}
      </div>

      {empty ? (
        <EmptyState>
          {state === "analyzing"
            ? "Talentpool-Suche läuft. Evaluation API bewertet Profile …"
            : "Sourcing Run starten, um Kandidaten zu bewerten."}
        </EmptyState>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {candidates.map((c, i) => (
            <CandidateRow
              key={c.id}
              c={c}
              channel={selectedChannels[c.id] || c.channel}
              selected={selectedId === c.id}
              dim={i >= 3}
              onClick={() => onSelect(c.id)}
              delay={i * 70}
              approvalStatus={showApprovalCol && i < 3 ? approvals[c.id] : null}
            />
          ))}
        </div>
      )}
    </Card>
  );
};

const EmptyState = ({ children }) => (
  <div
    style={{
      padding: "40px 20px",
      borderRadius: 12,
      border: `1px dashed ${T.borderStrong}`,
      color: T.textDim,
      fontSize: 13.5,
      textAlign: "center",
      background: "rgba(255,255,255,0.015)",
    }}
  >
    {children}
  </div>
);

// ---------- Panel 3 sub-components ----------
const DetailMetric = ({ label, value, accent }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
    <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint }}>
      {label}
    </div>
    <div style={{ fontSize: 16, fontWeight: 600, color: accent ? T.yellow : T.text, fontVariantNumeric: "tabular-nums" }}>
      {value}
    </div>
  </div>
);

const ChannelOptions = ({ channels, selectedChannel, onSelect }) => (
  <div>
    <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint, marginBottom: 8 }}>
      Verfügbare Kontaktkanäle
    </div>
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {(channels || []).map((channel) => (
        <button
          key={channel}
          onClick={() => onSelect(channel)}
          title={`${channel} Entwurf anzeigen`}
          style={{
            border: `1px solid ${selectedChannel === channel ? "rgba(255,215,0,0.42)" : T.border}`,
            background: selectedChannel === channel ? "rgba(255,215,0,0.10)" : "transparent",
            color: T.text,
            borderRadius: 999,
            padding: 0,
            cursor: "pointer",
          }}
        >
          <ChannelBadge channel={channel} />
        </button>
      ))}
    </div>
  </div>
);

const InteractionHistory = ({ interactions }) => (
  <div>
    <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint, marginBottom: 8 }}>
      Frühere Interaktionen
    </div>
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {(interactions || []).map((interaction, index) => (
        <div
          key={`${interaction}-${index}`}
          style={{
            padding: "9px 11px",
            borderRadius: 8,
            border: `1px solid ${T.border}`,
            background: "rgba(255,255,255,0.02)",
            color: T.textDim,
            fontSize: 12.5,
            lineHeight: 1.45,
          }}
        >
          {interaction}
        </div>
      ))}
    </div>
  </div>
);

const WorkdayButton = ({ candidate }) => (
  <button
    onClick={() => window.open(candidate.workday_profile_url, "_blank", "noopener,noreferrer")}
    style={{
      padding: "10px 12px",
      borderRadius: 10,
      border: `1px solid ${T.borderStrong}`,
      background: "rgba(255,255,255,0.03)",
      color: T.text,
      fontWeight: 650,
      fontSize: 12.5,
      cursor: "pointer",
      textAlign: "left",
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
    }}
  >
    <span
      aria-hidden
      style={{
        width: 18,
        height: 18,
        borderRadius: 5,
        display: "grid",
        placeItems: "center",
        background: "#f5a623",
        color: "#17202a",
        fontWeight: 900,
        fontSize: 11,
      }}
    >
      W
    </span>
    Workday Profil öffnen
  </button>
);

const VoiceNumberInput = ({ value, onChange }) => (
  <label style={{ display: "flex", flexDirection: "column", gap: 7 }}>
    <span style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint }}>
      Telefonnummer
    </span>
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={DEFAULT_PHONE_NUMBER}
      style={{
        width: "100%",
        boxSizing: "border-box",
        padding: "10px 12px",
        borderRadius: 10,
        border: `1px solid ${T.borderStrong}`,
        background: "rgba(0,0,0,0.20)",
        color: T.text,
        fontSize: 13.5,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        outline: "none",
      }}
    />
  </label>
);

const OutreachDraftModal = ({ candidate, channel, draft, phoneNumber, onDraftChange, onPhoneNumberChange, onClose }) => {
  if (!candidate || !channel) return null;
  const isVoice = channel === "Voice Call";
  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        background: "rgba(0,0,0,0.58)",
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
      onMouseDown={onClose}
    >
      <div
        onMouseDown={(e) => e.stopPropagation()}
        style={{
          width: "min(720px, 100%)",
          borderRadius: 14,
          border: `1px solid ${T.borderStrong}`,
          background: T.surface2,
          boxShadow: "0 24px 80px rgba(0,0,0,0.45)",
          padding: 22,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 14 }}>
          <div>
            <div style={{ fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase", color: T.textFaint, marginBottom: 7 }}>
              Entwurf bearbeiten
            </div>
            <div style={{ fontSize: 20, fontWeight: 650, color: T.text }}>
              {channel} an {candidate.name}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Entwurf schließen"
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              border: `1px solid ${T.border}`,
              background: "rgba(255,255,255,0.03)",
              color: T.textDim,
              cursor: "pointer",
              fontSize: 20,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {isVoice && (
          <VoiceNumberInput value={phoneNumber} onChange={onPhoneNumberChange} />
        )}

        <label style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          <span style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint }}>
            {isVoice ? "Voice-Call Intro" : "Nachricht"}
          </span>
          <textarea
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            rows={isVoice ? 7 : 11}
            style={{
              width: "100%",
              boxSizing: "border-box",
              resize: "vertical",
              minHeight: isVoice ? 140 : 220,
              padding: 13,
              borderRadius: 12,
              border: `1px solid ${T.borderStrong}`,
              background: "rgba(0,0,0,0.22)",
              color: T.text,
              fontSize: 13.5,
              lineHeight: 1.55,
              fontFamily: "inherit",
              outline: "none",
            }}
          />
        </label>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={onClose}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid rgba(255,215,0,0.4)",
              background: T.amber,
              color: "#1A1300",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Entwurf übernehmen
          </button>
        </div>
      </div>
    </div>
  );
};

const ApprovalCard = ({ candidate, onApprove, onDecline, status, progress }) => {
  // Per-candidate copy
  const reason =
    candidate.id === "miriam" || candidate.channel === "Voice Call"
      ? "Konflikt-Check: Strategische Personalplanung erkannt. Persönlicher Outreach (Voice Call) benötigt manuelle Freigabe."
      : `Konflikt-Check abgeschlossen. ${candidate.channel} an ${candidate.name} benötigt einzelne Freigabe.`;

  if (status === "approved") {
    return (
      <div
        style={{
          borderRadius: 14,
          padding: 16,
          background: "rgba(127,178,131,0.06)",
          border: "1px solid rgba(127,178,131,0.28)",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            width: 28, height: 28, borderRadius: 999,
            background: "rgba(127,178,131,0.18)",
            border: "1px solid rgba(127,178,131,0.4)",
            display: "grid", placeItems: "center", color: T.green, fontWeight: 700,
          }}
        >✓</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: T.text }}>Outreach freigegeben</div>
          <div style={{ fontSize: 12.5, color: T.textDim }}>
            {candidate.channel} für {candidate.name} bereit. {progress.approved} von {progress.total} freigegeben.
          </div>
        </div>
      </div>
    );
  }

  if (status === "declined") {
    return (
      <div
        style={{
          borderRadius: 14,
          padding: 16,
          background: "rgba(174,183,179,0.05)",
          border: `1px solid ${T.borderStrong}`,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            width: 28, height: 28, borderRadius: 999,
            background: "rgba(174,183,179,0.10)",
            border: `1px solid ${T.borderStrong}`,
            display: "grid", placeItems: "center", color: T.textDim, fontWeight: 700,
          }}
        >–</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: T.text }}>Abgelehnt</div>
          <div style={{ fontSize: 12.5, color: T.textDim }}>
            Outreach an {candidate.name} wird nicht versendet.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        borderRadius: 14,
        padding: 18,
        background:
          "linear-gradient(180deg, rgba(232,180,58,0.10), rgba(232,180,58,0.04))",
        border: "1px solid rgba(232,180,58,0.32)",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        position: "relative",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: "rgba(232,180,58,0.18)",
              border: "1px solid rgba(232,180,58,0.4)",
              display: "grid",
              placeItems: "center",
              color: T.amber,
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            !
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: T.text }}>
            Einzelfreigabe erforderlich
          </div>
        </div>
        <span style={{ fontSize: 11.5, color: T.textFaint, fontVariantNumeric: "tabular-nums" }}>
          {progress.approved + progress.declined}/{progress.total} entschieden
        </span>
      </div>
      <div style={{ fontSize: 13.5, color: T.textDim, lineHeight: 1.55 }}>
        {reason}
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={onApprove}
          style={{
            flex: 1,
            padding: "12px 14px",
            borderRadius: 10,
            background: T.amber,
            color: "#1A1300",
            fontWeight: 700,
            fontSize: 13.5,
            border: "none",
            cursor: "pointer",
            letterSpacing: 0.2,
          }}
        >
          Freigeben
        </button>
        <button
          onClick={onDecline}
          style={{
            padding: "12px 14px",
            borderRadius: 10,
            background: "transparent",
            color: T.textDim,
            fontWeight: 500,
            fontSize: 13.5,
            border: `1px solid ${T.borderStrong}`,
            cursor: "pointer",
          }}
        >
          Ablehnen
        </button>
      </div>
    </div>
  );
};

const OutreachList = ({ actions }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
    <div style={{ fontSize: 12, color: T.textFaint, letterSpacing: 1.4, textTransform: "uppercase", marginBottom: 4 }}>
      Outreach Status
    </div>
    {actions.map((a) => (
      <div
        key={a.id}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 12px",
          borderRadius: 10,
          border: `1px solid ${T.border}`,
          background: "rgba(255,255,255,0.02)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ fontSize: 13.5, color: T.text, fontWeight: 500 }}>{a.name}</div>
          <div style={{ fontSize: 12, color: T.textDim }}>{a.message_excerpt}</div>
        </div>
        <StatusPill tone={a.status === "sent" ? "ok" : "accent"}>
          {a.status === "sent" ? "Gesendet" : "Bereit"}
        </StatusPill>
      </div>
    ))}
  </div>
);

const VoiceCallPanel = ({ calling, completed, candidate, phoneNumber, onPhoneNumberChange, onStart, callLog, error }) => {
  return (
    <div
      style={{
        borderRadius: 14,
        padding: 18,
        background: "linear-gradient(180deg, rgba(255,215,0,0.05), rgba(255,215,0,0.01))",
        border: "1px solid rgba(255,215,0,0.22)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {calling && (
        <div
          aria-hidden
          style={{
            position: "absolute",
            inset: -40,
            background:
              "radial-gradient(300px 160px at 50% 50%, rgba(255,215,0,0.18), transparent 70%)",
            animation: "pulseGlow 1800ms ease-in-out infinite",
            pointerEvents: "none",
          }}
        />
      )}
      <div style={{ position: "relative", display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 999,
                background: "rgba(255,215,0,0.15)",
                border: "1px solid rgba(255,215,0,0.4)",
                display: "grid",
                placeItems: "center",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={T.yellow} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </div>
            <div>
              <div style={{ fontSize: 14.5, fontWeight: 600, color: T.text }}>Live Voice Outreach</div>
              <div style={{ fontSize: 12, color: T.textDim, marginTop: 2 }}>
                {calling ? "Wählt angegebene Nummer…" : error ? "Fehler" : completed ? "Call gestartet" : "Anruf bereit"}
              </div>
            </div>
          </div>
          <StatusPill tone={error ? "err" : completed ? "ok" : calling ? "accent" : "accent"}>
            {error ? "Fehler" : completed ? "Gestartet" : calling ? "Wählt…" : "Bereit"}
          </StatusPill>
        </div>

        <div style={{ fontSize: 12.5, color: T.textDim, lineHeight: 1.5 }}>
          Ruft {candidate.name} unter der unten angegebenen Nummer an. Die Nummer kann vor dem Start überschrieben werden.
        </div>

        <VoiceNumberInput value={phoneNumber} onChange={onPhoneNumberChange} />

        <button
          onClick={onStart}
          disabled={calling}
          style={{
            padding: "12px 14px",
            borderRadius: 10,
            border: "1px solid rgba(255,215,0,0.4)",
            background: calling
              ? "rgba(255,215,0,0.15)"
              : "linear-gradient(180deg, #FFE34A, #F2C400)",
            color: calling ? T.yellow : "#1A1300",
            fontWeight: 700,
            fontSize: 13.5,
            cursor: calling ? "default" : "pointer",
            boxShadow: calling ? "none" : "0 10px 24px -10px rgba(255,215,0,0.4)",
          }}
        >
          {calling
            ? "Wählt angegebene Nummer…"
            : error
                ? "Erneut versuchen"
                : completed
                  ? "Live Call erneut starten"
                  : "Live Call starten"}
        </button>

        {completed && callLog && (
          <div
            style={{
              borderRadius: 10,
              border: `1px solid ${T.border}`,
              background: "rgba(0,0,0,0.25)",
              padding: 12,
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: T.textFaint, fontFamily: "ui-monospace, monospace" }}>
              <span>callSid: {callLog.callSid}</span>
              <span>{callLog.timestamp}</span>
            </div>
            <div style={{ fontSize: 12.5, color: T.text, lineHeight: 1.55, fontStyle: "italic" }}>
              „{callLog.transcript_excerpt}"
            </div>
          </div>
        )}

        {error && (
          <div
            style={{
              padding: 12,
              borderRadius: 10,
              border: "1px solid rgba(217,116,104,0.3)",
              background: "rgba(217,116,104,0.06)",
              color: T.red,
              fontSize: 12.5,
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

// ---------- Panel 3 ----------
const SelectedPanel = ({
  state,
  selected,
  approvals,
  selectedChannel,
  phoneNumber,
  onSelectChannel,
  onPhoneNumberChange,
  onApprove,
  onDecline,
  onCall,
  callingCandidateId,
  callLog,
  callError,
  outreachActions,
}) => {
  if (state === "idle" || state === "analyzing") {
    return (
      <Card padding={24} style={{ height: "100%" }}>
        <div style={{ fontSize: 18, fontWeight: 600, color: T.text, marginBottom: 18 }}>
          Kandidat
        </div>
        <EmptyState>Sourcing Run starten, um Kandidatendetails anzuzeigen.</EmptyState>
      </Card>
    );
  }
  if (!selected) return null;

  const isTop3 = selected.rank <= 3;
  const approvalStatus = approvals[selected.id]; // pending | approved | declined | undefined
  const approvalActive = state === "paused_for_recruiter_approval" || state === "outreach_ready" || state === "call_in_progress" || state === "call_completed";

  const total = 3;
  const approvedCount = Object.values(approvals).filter((s) => s === "approved").length;
  const declinedCount = Object.values(approvals).filter((s) => s === "declined").length;
  const progress = { approved: approvedCount, declined: declinedCount, total };

  const voiceAvailable = selected.available_channels?.includes("Voice Call");

  // Voice panel only after the candidate has been individually approved.
  const showVoice =
    voiceAvailable &&
    approvalStatus === "approved" &&
    (
      state === "paused_for_recruiter_approval" ||
      state === "outreach_ready" ||
      state === "call_in_progress" ||
      state === "call_completed"
    );

  // Outreach action for the selected candidate (if any)
  const myAction = outreachActions.find((a) => a.candidate_id === selected.id);

  return (
    <Card padding={24} style={{ height: "100%" }} glow>
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
          <div>
            <div style={{ fontSize: 11, letterSpacing: 1.6, textTransform: "uppercase", color: T.textFaint, marginBottom: 8 }}>
              Ausgewählt · #{String(selected.rank).padStart(2, "0")}
            </div>
            <div style={{ fontSize: 24, fontWeight: 600, color: T.text, letterSpacing: -0.3 }}>
              {selected.name}
            </div>
            <div style={{ fontSize: 13.5, color: T.textDim, marginTop: 4 }}>
              {selected.descriptor} · {selected.source}
            </div>
          </div>
          <ChannelBadge channel={selectedChannel || selected.channel} />
        </div>

        {/* Metrics */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 16,
            padding: "14px 16px",
            borderRadius: 12,
            background: "rgba(255,255,255,0.02)",
            border: `1px solid ${T.border}`,
          }}
        >
          <DetailMetric label="Match Score" value={`${Math.round(selected.score * 100)}%`} accent />
          <DetailMetric label="Vector Sim." value={selected.vector_similarity.toFixed(2)} />
          <DetailMetric label="Channel" value={selectedChannel || selected.channel} />
        </div>

        {/* Rationale */}
        <div>
          <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: T.textFaint, marginBottom: 8 }}>
            Begründung
          </div>
          <div style={{ fontSize: 13.5, color: T.text, lineHeight: 1.6 }}>
            {selected.rationale}
          </div>
        </div>

        <ChannelOptions
          channels={selected.available_channels}
          selectedChannel={selectedChannel}
          onSelect={(channel) => onSelectChannel(selected.id, channel)}
        />

        <InteractionHistory interactions={selected.interaction_summary} />

        {selected.has_workday_profile && selected.workday_profile_url && (
          <WorkdayButton candidate={selected} />
        )}

        {/* Risk flags */}
        {selected.risk_flags.length > 0 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {selected.risk_flags.map((f) => (
              <StatusPill key={f} tone="warn">{riskFlagLabel(f)}</StatusPill>
            ))}
          </div>
        )}

        {/* Per-candidate approval (top 3 only) */}
        {approvalActive && isTop3 && approvalStatus && (
          <ApprovalCard
            candidate={{ ...selected, channel: selectedChannel || selected.channel }}
            status={approvalStatus}
            progress={progress}
            onApprove={() => onApprove(selected.id)}
            onDecline={() => onDecline(selected.id)}
          />
        )}

        {/* Bottom-3 short note */}
        {approvalActive && !isTop3 && (
          <div
            style={{
              padding: "12px 14px",
              borderRadius: 10,
              border: `1px solid ${T.border}`,
              background: "rgba(255,255,255,0.02)",
              color: T.textDim,
              fontSize: 12.5,
            }}
          >
            Nicht in Top 3 — kein Outreach vorgesehen.
          </div>
        )}

        {/* Outreach status for this candidate */}
        {myAction && (
          <OutreachList actions={[{ ...myAction, name: selected.name }]} />
        )}

        {/* Voice for Miriam after approval */}
        {showVoice && (
          <VoiceCallPanel
            calling={callingCandidateId === selected.id}
            completed={Boolean(callLog)}
            candidate={selected}
            phoneNumber={phoneNumber}
            onPhoneNumberChange={(value) => onPhoneNumberChange(selected.id, value)}
            onStart={() => onCall(selected.id)}
            callLog={callLog}
            error={callError}
          />
        )}
      </div>
    </Card>
  );
};

// ---------- Audit Timeline ----------
const AuditTimeline = ({ completedSteps, activeStep }) => {
  return (
    <div
      style={{
        padding: "16px 24px",
        borderTop: `1px solid ${T.border}`,
        background: "rgba(11,17,23,0.6)",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div style={{ fontSize: 11, letterSpacing: 1.6, textTransform: "uppercase", color: T.textFaint, marginRight: 12, whiteSpace: "nowrap" }}>
        Audit Trail
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flex: 1, overflow: "hidden" }}>
        {AUDIT_STEPS.map((s, i) => {
          const done = completedSteps.includes(s.id);
          const active = activeStep === s.id;
          const color = done ? T.green : active ? T.yellow : T.textFaint;
          return (
            <React.Fragment key={s.id}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 10px",
                  borderRadius: 999,
                  border: `1px solid ${done ? "rgba(127,178,131,0.25)" : active ? "rgba(255,215,0,0.32)" : T.border}`,
                  background: active ? T.yellowSoft : done ? "rgba(127,178,131,0.06)" : "transparent",
                  whiteSpace: "nowrap",
                }}
              >
                <Dot color={color} size={6} />
                <span style={{ fontSize: 11.5, color: done || active ? T.text : T.textFaint, letterSpacing: 0.1 }}>
                  {s.label}
                </span>
              </div>
              {i < AUDIT_STEPS.length - 1 && (
                <div style={{ width: 12, height: 1, background: T.border }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

// ---------- Banner ----------
const ErrorBanner = ({ children }) => (
  <div
    style={{
      padding: "10px 24px",
      background: "rgba(217,116,104,0.08)",
      borderBottom: "1px solid rgba(217,116,104,0.2)",
      color: T.red,
      fontSize: 12.5,
      display: "flex",
      alignItems: "center",
      gap: 10,
    }}
  >
    <Dot color={T.red} />
    {children}
  </div>
);

// ---------- App ----------
function App() {
  const [page, setPage] = useState("briefing"); // briefing | cockpit
  const [positionId, setPositionId] = useState(POSITIONS[0].id);
  const [positionsState, setPositionsState] = useState(POSITIONS);
  const position = useMemo(
    () => positionsState.find((p) => p.id === positionId) || positionsState[0],
    [positionsState, positionId]
  );

  const [state, setState] = useState("idle"); // idle | analyzing | paused_for_recruiter_approval | outreach_ready | call_in_progress | call_completed
  const [candidates, setCandidates] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [activeStep, setActiveStep] = useState(null);
  const [callLogsByCandidate, setCallLogsByCandidate] = useState({});
  const [callErrorsByCandidate, setCallErrorsByCandidate] = useState({});
  const [callingCandidateId, setCallingCandidateId] = useState(null);
  const [outreachActions, setOutreachActions] = useState([]);
  const [approvals, setApprovals] = useState({});
  const [backendOk, setBackendOk] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [voiceOk, setVoiceOk] = useState(false);
  const [selectedChannels, setSelectedChannels] = useState({});
  const [outreachDrafts, setOutreachDrafts] = useState({});
  const [phoneNumbers, setPhoneNumbers] = useState({});
  const [draftModal, setDraftModal] = useState(null);

  const cockpitUnlocked = state !== "idle";

  const selected = useMemo(
    () => candidates.find((c) => c.id === selectedId) || null,
    [candidates, selectedId]
  );

  const selectedContactChannel = useMemo(() => {
    if (!selected) return null;
    const preferred = selectedChannels[selected.id] || selected.channel;
    return selected.available_channels?.includes(preferred)
      ? preferred
      : selected.available_channels?.[0] || null;
  }, [selected, selectedChannels]);

  const selectedPhoneNumber = selected
    ? phoneNumbers[selected.id] || defaultPhoneForCandidate(selected)
    : DEFAULT_PHONE_NUMBER;

  const setDefaultPhoneNumbers = useCallback((uiCandidates) => {
    setPhoneNumbers((prev) => {
      const next = { ...prev };
      uiCandidates.forEach((candidate) => {
        if (candidate.available_channels?.includes("Voice Call") && !next[candidate.id]) {
          next[candidate.id] = defaultPhoneForCandidate(candidate);
        }
      });
      return next;
    });
  }, []);

  const openDraftForChannel = useCallback((candidateId, channel) => {
    const candidate = candidates.find((item) => item.id === candidateId);
    if (!candidate) return;

    setSelectedChannels((prev) => ({ ...prev, [candidateId]: channel }));
    setOutreachDrafts((prev) => {
      const key = draftKey(candidateId, channel);
      if (prev[key]) return prev;
      return { ...prev, [key]: defaultOutreachDraft(candidate, channel) };
    });
    if (channel === "Voice Call") {
      setPhoneNumbers((prev) => ({
        ...prev,
        [candidateId]: prev[candidateId] || defaultPhoneForCandidate(candidate),
      }));
    }
    setDraftModal({ candidateId, channel });
  }, [candidates]);

  const updatePhoneNumber = useCallback((candidateId, value) => {
    setPhoneNumbers((prev) => ({ ...prev, [candidateId]: value }));
  }, []);

  const hydrateFromStatus = useCallback(async () => {
    try {
      const payload = await apiRequest("/api/status");
      const uiCandidates = (payload.candidates || []).map(toUiCandidate);
      setBackendOk(true);
      setBackendError(null);
      setVoiceOk(Boolean(payload.voice?.live_call_ready));
      setState(payload.state || "idle");
      if (payload.job_id) {
        setPositionId(payload.job_id);
      }
      setCompletedSteps(stepsForState(payload.state));
      setCandidates(uiCandidates);
      setDefaultPhoneNumbers(uiCandidates);
      setOutreachActions((payload.outreach_actions || []).map(toUiAction));
      if (payload.approvals?.length) {
        setApprovals(approvalsToMap(payload.approvals));
      }
      if (uiCandidates.length > 0) {
        setSelectedId((current) => current || uiCandidates[0].id);
        setPage(payload.state === "idle" || payload.state === "seeded" ? "briefing" : "cockpit");
      }
      if (payload.state === "paused_for_recruiter_approval" && !payload.approvals?.length) {
        setApprovals({ katharina: "pending", daniel: "pending", miriam: "pending" });
      }
      if (
        !payload.approvals?.length &&
        (payload.state === "outreach_ready" || payload.state === "call_in_progress" || payload.state === "call_completed")
      ) {
        setApprovals({ katharina: "approved", daniel: "approved", miriam: "approved" });
      }
      if (payload.call_logs?.length) {
        setCallLogsByCandidate(
          payload.call_logs.reduce((acc, log) => {
            acc[log.candidate_id] = {
              ...log,
              transcript_excerpt: "Outbound Voice Call wurde über den Backend-Provider gestartet.",
            };
            return acc;
          }, {})
        );
      }
    } catch (error) {
      setBackendOk(false);
      setBackendError(error.message);
    }
  }, [setDefaultPhoneNumbers]);

  useEffect(() => {
    hydrateFromStatus();
  }, [hydrateFromStatus]);

  const advanceStep = (id, delay = 0) =>
    new Promise((resolve) => {
      setTimeout(() => {
        setActiveStep(id);
        setTimeout(() => {
          setCompletedSteps((prev) => (prev.includes(id) ? prev : [...prev, id]));
          setActiveStep(null);
          resolve();
        }, 550);
      }, delay);
    });

  const onPickPosition = (id) => setPositionId(id);
  const onUpdatePosition = (patch) => {
    setPositionsState((prev) =>
      prev.map((p) => (p.id === positionId ? { ...p, ...patch } : p))
    );
  };

  const onStart = async () => {
    if (state !== "idle" && state !== "seeded") return;
    setState("analyzing");
    setPage("cockpit");
    setCandidates([]);
    setSelectedId(null);
    setCompletedSteps([]);
    setCallLogsByCandidate({});
    setCallErrorsByCandidate({});
    setCallingCandidateId(null);
    setOutreachActions([]);
    setApprovals({});
    setSelectedChannels({});
    setOutreachDrafts({});
    setPhoneNumbers({});
    setDraftModal(null);

    try {
      await apiRequest("/api/seed", { method: "POST" });
      await advanceStep("anf", 200);
      await advanceStep("vec", 100);
      await advanceStep("eval", 100);

      const payload = await apiRequest("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: position.id }),
      });
      const uiCandidates = (payload.candidates || []).map(toUiCandidate);
      setBackendOk(true);
      setBackendError(null);
      setVoiceOk(Boolean(payload.voice?.live_call_ready));
      setCandidates(uiCandidates);
      setDefaultPhoneNumbers(uiCandidates);
      setSelectedId(uiCandidates[0]?.id || null);
      if (payload.approvals?.length) {
        setApprovals(approvalsToMap(payload.approvals));
      }

      await advanceStep("konflikt", 400);
      if (!payload.approvals?.length) {
        setApprovals({ katharina: "pending", daniel: "pending", miriam: "pending" });
      }
      setState(payload.state || "paused_for_recruiter_approval");
    } catch (error) {
      setBackendOk(false);
      setBackendError(error.message);
      setCandidates(FIXTURE_CANDIDATES);
      setDefaultPhoneNumbers(FIXTURE_CANDIDATES.map(toUiCandidate));
      setSelectedId("c1");
      await advanceStep("konflikt", 400);
      setApprovals({ c1: "pending", c2: "pending", c3: "pending" });
      setState("paused_for_recruiter_approval");
    }
  };

  const onReset = async () => {
    setState("idle");
    setPage("briefing");
    setCandidates([]);
    setSelectedId(null);
    setCompletedSteps([]);
    setActiveStep(null);
    setCallLogsByCandidate({});
    setCallErrorsByCandidate({});
    setCallingCandidateId(null);
    setOutreachActions([]);
    setApprovals({});
    setSelectedChannels({});
    setOutreachDrafts({});
    setPhoneNumbers({});
    setDraftModal(null);
    try {
      await apiRequest("/api/reset", { method: "POST" });
      setBackendOk(true);
      setBackendError(null);
    } catch (error) {
      setBackendOk(false);
      setBackendError(error.message);
    }
  };

  const tickFreigabeOnce = useCallback(() => {
    setCompletedSteps((prev) => prev.includes("freigabe") ? prev : [...prev, "freigabe"]);
  }, []);
  const tickOutreachOnce = useCallback(() => {
    setCompletedSteps((prev) => prev.includes("outreach") ? prev : [...prev, "outreach"]);
  }, []);

  const onApproveOne = async (candidateId) => {
    const c = candidates.find((x) => x.id === candidateId) || FIXTURE_CANDIDATES.find((x) => x.id === candidateId);
    if (!c) return;
    const chosenChannel = selectedChannels[candidateId] || c.channel;
    const nextApprovals = { ...approvals, [candidateId]: "approved" };
    setApprovals(nextApprovals);
    setOutreachActions((prev) => {
      if (prev.find((a) => a.candidate_id === candidateId)) return prev;
      const isVoice = chosenChannel === "Voice Call";
      return [
        ...prev,
        {
          id: "o_" + candidateId,
          candidate_id: candidateId,
          channel: chosenChannel,
          status: isVoice ? "ready" : "sent",
          message_excerpt: isVoice ? "Voice Call · vorbereitet" : `${chosenChannel} · gesendet`,
          created_at: new Date().toISOString(),
        },
      ];
    });
    tickFreigabeOnce();
    tickOutreachOnce();
    try {
      const payload = await apiRequest(`/api/approvals/${candidateId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: "approved" }),
      });
      setBackendOk(true);
      setBackendError(null);
      setVoiceOk(Boolean(payload.voice?.live_call_ready));
      setApprovals(approvalsToMap(payload.approvals));
      setOutreachActions((payload.outreach_actions || []).map(toUiAction).map((action) => {
        if (action.candidate_id !== candidateId || !chosenChannel) return action;
        const isVoice = chosenChannel === "Voice Call";
        return {
          ...action,
          channel: chosenChannel,
          status: isVoice ? "ready" : action.status,
          message_excerpt: isVoice ? "Voice Call · vorbereitet" : `${chosenChannel} · gesendet`,
        };
      }));
      setState(payload.state || state);
    } catch (error) {
      setBackendOk(false);
      setBackendError(error.message);
    }
  };

  const onDeclineOne = async (candidateId) => {
    const nextApprovals = { ...approvals, [candidateId]: "declined" };
    setApprovals(nextApprovals);
    tickFreigabeOnce();
    try {
      const payload = await apiRequest(`/api/approvals/${candidateId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: "declined" }),
      });
      setBackendOk(true);
      setBackendError(null);
      setVoiceOk(Boolean(payload.voice?.live_call_ready));
      setApprovals(approvalsToMap(payload.approvals));
      setOutreachActions((payload.outreach_actions || []).map(toUiAction));
      setState(payload.state || state);
    } catch (error) {
      setBackendOk(false);
      setBackendError(error.message);
    }
  };

  const onCall = async (candidateId) => {
    const candidate = candidates.find((item) => item.id === candidateId);
    const targetPhoneNumber = (phoneNumbers[candidateId] || defaultPhoneForCandidate(candidate)).trim();
    const recruiterIntro =
      outreachDrafts[draftKey(candidateId, "Voice Call")] || defaultOutreachDraft(candidate, "Voice Call");
    const previousState = state;
    setState("call_in_progress");
    setCallingCandidateId(candidateId);
    setCallErrorsByCandidate((prev) => ({ ...prev, [candidateId]: null }));
    try {
      const payload = await apiRequest(`/api/call/${candidateId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_phone_number: targetPhoneNumber,
          recruiter_intro: recruiterIntro,
        }),
      });
      await advanceStep("call", 100);
      setBackendOk(true);
      setBackendError(null);
      setCallLogsByCandidate((prev) => ({
        ...prev,
        [candidateId]: {
          ...payload,
          timestamp: new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          transcript_excerpt: payload.message || "Outbound Voice Call wurde über den Backend-Provider gestartet.",
        },
      }));
      setCallingCandidateId(null);
      setState(payload.state || "call_completed");
    } catch (error) {
      setBackendOk(true);
      setCallErrorsByCandidate((prev) => ({ ...prev, [candidateId]: error.message }));
      setCallingCandidateId(null);
      setState(previousState);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: T.bg,
        color: T.text,
        fontFamily:
          "ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', Helvetica, Arial",
        display: "flex",
        flexDirection: "column",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          background:
            "radial-gradient(900px 500px at 80% -10%, rgba(255,215,0,0.06), transparent 60%), radial-gradient(700px 400px at -10% 100%, rgba(255,215,0,0.03), transparent 60%)",
        }}
      />

      <TopBar
        backendOk={backendOk}
        voiceOk={voiceOk}
        page={page}
        setPage={setPage}
        position={position}
        cockpitUnlocked={cockpitUnlocked}
      />

      {!backendOk && (
        <ErrorBanner>
          Backend nicht erreichbar oder Aktion fehlgeschlagen: {backendError || "UI zeigt lokale Demo-Daten."}
        </ErrorBanner>
      )}

      {page === "briefing" ? (
        <BriefingPage
          position={position}
          positions={positionsState}
          onPickPosition={onPickPosition}
          onUpdatePosition={onUpdatePosition}
          onStart={onStart}
          onReset={onReset}
          state={state}
        />
      ) : (
        <div
          style={{
            flex: 1,
            padding: "28px",
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.3fr) minmax(420px, 1fr)",
            gap: 20,
            position: "relative",
            zIndex: 1,
          }}
        >
          <ShortlistPanel
            state={state}
            candidates={candidates}
            selectedId={selectedId}
            onSelect={setSelectedId}
            approvals={approvals}
            selectedChannels={selectedChannels}
          />
          <SelectedPanel
            state={state}
            selected={selected}
            approvals={approvals}
            selectedChannel={selectedContactChannel}
            phoneNumber={selectedPhoneNumber}
            onSelectChannel={openDraftForChannel}
            onPhoneNumberChange={updatePhoneNumber}
            onApprove={onApproveOne}
            onDecline={onDeclineOne}
            onCall={onCall}
            callingCandidateId={callingCandidateId}
            callLog={selected ? callLogsByCandidate[selected.id] : null}
            callError={selected ? callErrorsByCandidate[selected.id] : null}
            outreachActions={outreachActions}
          />
        </div>
      )}

      {draftModal && (
        <OutreachDraftModal
          candidate={candidates.find((candidate) => candidate.id === draftModal.candidateId)}
          channel={draftModal.channel}
          draft={
            outreachDrafts[draftKey(draftModal.candidateId, draftModal.channel)]
            || defaultOutreachDraft(
              candidates.find((candidate) => candidate.id === draftModal.candidateId),
              draftModal.channel
            )
          }
          phoneNumber={phoneNumbers[draftModal.candidateId] || defaultPhoneForCandidate(candidates.find((candidate) => candidate.id === draftModal.candidateId))}
          onDraftChange={(value) => {
            setOutreachDrafts((prev) => ({
              ...prev,
              [draftKey(draftModal.candidateId, draftModal.channel)]: value,
            }));
          }}
          onPhoneNumberChange={(value) => updatePhoneNumber(draftModal.candidateId, value)}
          onClose={() => setDraftModal(null)}
        />
      )}

      {page === "cockpit" && (
        <AuditTimeline completedSteps={completedSteps} activeStep={activeStep} />
      )}
    </div>
  );
}
export default App;

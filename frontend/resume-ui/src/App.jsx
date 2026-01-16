import StatusBar from "./components/StatusBar";
import LeftPanel from "./components/LeftPanel";
import RightPanel from "./components/RightPanel";
import { useEffect, useState } from "react";
import {
  getResume,
  scoreVariant,
  getBulletImpact,
  applyRemovals,
  listVariants
} from "./api";

const FLOW = {
  IDLE: "idle",
  VARIANT_SELECTED: "variant_selected",
  JOB_ENTERED: "job_entered",
  SCORED: "scored",
  REVIEWING: "reviewing",
  READY_TO_APPLY: "ready_to_apply",
  APPLIED: "applied"
};

const STEP_LABELS = {
  [FLOW.IDLE]: "Initializing system",
  [FLOW.VARIANT_SELECTED]: "Step 1 — Review resume & select job",
  [FLOW.JOB_ENTERED]: "Step 2 — Confirm job description",
  [FLOW.SCORED]: "Step 3 — Resume scored",
  [FLOW.REVIEWING]: "Step 4 — Review bullet impact",
  [FLOW.READY_TO_APPLY]: "Step 5 — Apply decisions",
  [FLOW.APPLIED]: "Step 6 — Changes applied"
};

const ALLOWED_TRANSITIONS = {
  [FLOW.IDLE]: [FLOW.VARIANT_SELECTED],
  [FLOW.VARIANT_SELECTED]: [FLOW.JOB_ENTERED],
  [FLOW.JOB_ENTERED]: [FLOW.SCORED],
  [FLOW.SCORED]: [FLOW.REVIEWING],
  [FLOW.REVIEWING]: [FLOW.READY_TO_APPLY],
  [FLOW.READY_TO_APPLY]: [FLOW.APPLIED]
};

function canTransition(from, to) {
  return ALLOWED_TRANSITIONS[from]?.includes(to);
}

function App() {
  const [resume, setResume] = useState(null);
  const [error, setError] = useState(null);

  const [flow, setFlow] = useState(FLOW.IDLE);
  const [job, setJob] = useState("");
  const [jobCollapsed, setJobCollapsed] = useState(false);
  const [score, setScore] = useState(null);
  const [impacts, setImpacts] = useState(null);

  const [backendStatus, setBackendStatus] = useState("checking");
  const [activeVariant, setActiveVariant] = useState(null);
  const [lastScoredAt, setLastScoredAt] = useState(null);

  const [loading, setLoading] = useState(false);
  const [uiError, setUiError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  function safeSetFlow(next) {
    setFlow(prev => (canTransition(prev, next) ? next : prev));
  }

  const isFinal = flow === FLOW.APPLIED;

  useEffect(() => {
    fetch(import.meta.env.VITE_API_BASE + "/")
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));

    getResume()
      .then(data => {
        setResume(data);
        safeSetFlow(FLOW.VARIANT_SELECTED);
      })
      .catch(err => setError(err.message));

    listVariants()
      .then(v => setActiveVariant(v.active))
      .catch(() => setActiveVariant("unknown"));
  }, []);

  if (error) return <pre>Error: {error}</pre>;
  if (!resume) return <p>Loading…</p>;

  return (
    <div style={{ minHeight: "100vh", background: "#f7f7f7" }}>
      
      <StatusBar
        backendStatus={backendStatus}
        activeVariant={activeVariant}
        lastScoredAt={lastScoredAt}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "2rem",
          padding: "2rem"
        }}
      >
        <LeftPanel
          flow={flow}
          resume={resume}
          job={job}
          setJob={setJob}
          jobCollapsed={jobCollapsed}
          setJobCollapsed={setJobCollapsed}
          loading={loading}
          successMsg={successMsg}
          STEP_LABELS={STEP_LABELS}
          FLOW={FLOW}
          safeSetFlow={safeSetFlow}
          scoreVariant={scoreVariant}
          setScore={setScore}
          setLastScoredAt={setLastScoredAt}
          applyRemovals={applyRemovals}
          setLoading={setLoading}
        />
        <RightPanel
          flow={flow}
          score={score}
          impacts={impacts}
          FLOW={FLOW}
        />
      </div>
    </div>
  );
}

export default App;
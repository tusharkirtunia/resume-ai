import { useEffect, useState } from "react";
import { getResume, scoreVariant, getBulletImpact, applyRemovals } from "./api";

const FLOW = {
  IDLE: "idle",
  VARIANT_SELECTED: "variant_selected",
  JOB_ENTERED: "job_entered",
  SCORED: "scored",
  REVIEWING: "reviewing",
  READY_TO_APPLY: "ready_to_apply",
  APPLIED: "applied"
};

function App() {
  const [resume, setResume] = useState(null);
  const [error, setError] = useState(null);
  const [flow, setFlow] = useState(FLOW.IDLE);
  const [job, setJob] = useState("");
  const [score, setScore] = useState(null);
  const [impacts, setImpacts] = useState(null);

  useEffect(() => {
    getResume()
      .then(data => {
        setResume(data);
        setFlow(FLOW.VARIANT_SELECTED);
      })
      .catch(err => setError(err.message));
  }, []);

  if (error) return <pre>Error: {error}</pre>;
  if (!resume) return <p>Loading…</p>;

  return (
  <div style={{ padding: "2rem" }}>
    <h1>Resume Decision Engine</h1>
    <p>Flow state: {flow}</p>

    {flow === FLOW.VARIANT_SELECTED && (
      <>
        <h2>Current Resume</h2>
        <pre>{JSON.stringify(resume, null, 2)}</pre>

        <h3>Enter Job Description</h3>
        <textarea
          rows={6}
          style={{ width: "100%" }}
          value={job}
          onChange={(e) => setJob(e.target.value)}
          placeholder="Paste the job description here"
        />

        <br /><br />

        <button
          disabled={!job.trim()}
          onClick={() => setFlow(FLOW.JOB_ENTERED)}
        >
          Confirm Job
        </button>
      </>
    )}

    {flow === FLOW.JOB_ENTERED && (
      <>
        <h2>Job Description</h2>
        <pre>{job}</pre>

        <button
          onClick={async () => {
            const result = await scoreVariant(job);
            setScore(result);
            setFlow(FLOW.SCORED);
          }}
        >
          Score Resume
        </button>
      </>
    )}

    {flow === FLOW.SCORED && (
      <>
        <h2>Scoring Result</h2>
        <pre>{JSON.stringify(score, null, 2)}</pre>
        <button
          onClick={async () => {
            const data = await getBulletImpact(job);
            setImpacts(data.impacts);
            setFlow(FLOW.REVIEWING);
          }}
        >
          Review Bullet Impact
        </button>
      </>
    )}

    {flow === FLOW.REVIEWING && (
      <>
        <h2>Bullet Impact Review</h2>
        <ul>
          {impacts.map((b, i) => (
            <li key={i}>
              <strong>Impact:</strong> {b.impact.toFixed(3)}<br />
              <em>{b.bullet}</em>
            </li>
          ))}
        </ul>

        <button onClick={() => setFlow(FLOW.READY_TO_APPLY)}>
          Continue
        </button>
      </>
    )}

    {flow === FLOW.READY_TO_APPLY && (
      <>
        <h2>Apply Bullet Decisions</h2>

        <button
          onClick={async () => {
            const result = await applyRemovals(job, { dryRun: true });
            alert(`Dry run complete. Bullets to remove: ${result.removed.length}`);
          }}
        >
          Dry Run
        </button>

        <br /><br />

        <button
          onClick={async () => {
            await applyRemovals(job, { confirm: true });
            setFlow(FLOW.APPLIED);
          }}
        >
          Confirm & Apply
        </button>
      </>
    )}

    {flow === FLOW.APPLIED && (
      <p>Changes applied successfully.</p>
    )}
  </div>
);
}

export default App;
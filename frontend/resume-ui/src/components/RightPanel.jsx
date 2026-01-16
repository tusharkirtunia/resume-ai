const [showExplanation, setShowExplanation] = useState(false);

function RightPanel({ flow, score, impacts, FLOW }) {
  return (
    <div style={{ background: "#fff", padding: "1.5rem", borderRadius: "8px" }}>
      <div style={{ marginBottom: "1rem" }}>
        <button
            type="button"
            onClick={() => setShowExplanation(v => !v)}
            style={{
                background: "none",
                border: "none",
                color: "#0066cc",
                fontSize: "0.8rem",
                cursor: "pointer",
                padding: 0
            }}
        >
            {showExplanation ? "Hide" : "Why am I seeing these results?"}
        </button>

        {showExplanation && (
            <div
                style={{
                    marginTop: "0.5rem",
                    fontSize: "0.8rem",
                    color: "#555",
                    lineHeight: "1.4",
                    background: "#f9f9f9",
                    padding: "0.75rem",
                    borderRadius: "6px"
            }}
          >
            The system compares your resume against the job description by analyzing
            skills, responsibilities, and relevance. Each bullet point is scored
            based on how strongly it aligns with the job requirements. Bullets with
            lower impact may reduce overall relevance and are suggested for review
            or removal.
          </div>
        )}
      </div>

      {flow === FLOW.SCORED && (
        <>
          <h3>Scoring Result</h3>
          <pre>{JSON.stringify(score, null, 2)}</pre>
        </>
      )}

      {flow === FLOW.REVIEWING && (
        <>
          <h3>Bullet Impact Review</h3>
          <ul>
            {impacts?.map((b, i) => (                
              <li key={i} style={{ marginBottom: "0.75rem" }}>
                <div>
                    <strong>{b.impact.toFixed(3)}</strong> — {b.bullet}
                </div>

                <div style={{ fontSize: "0.75rem", color: "#666", marginTop: "0.25rem" }}>
                    {b.impact > 0.7 && "Strong alignment with job requirements"}
                    {b.impact <= 0.7 && b.impact >= 0.4 && "Moderate relevance to the role"}
                    {b.impact < 0.4 && "Weak or generic alignment"}
                </div>
            </li>
            ))}
          </ul>
        </>
      )}

      {flow === FLOW.APPLIED && (
        <div
            style={{
                background: "#eef6ff",
                border: "1px solid #b3d4fc",
                padding: "1rem",
                borderRadius: "8px",
                fontSize: "0.9rem"
            }}
        >
            <h3 style={{ marginTop: 0 }}>Finalized</h3>

            <strong>Session completed.</strong>
            <p style={{ marginTop: "0.5rem" }}>
                The resume has been permanently modified.  
                This session is now read-only and cannot be undone.
            </p>
            
            <p style={{ fontSize: "0.8rem", color: "#555" }}>
                Changes were applied based on the provided job description and scoring rules.
            </p>

            <button
                style={{ marginTop: "1rem" }}
                title="This will reset the current session"
                onClick={() => window.location.reload()}
            >
                Start new session
            </button>
        </div>
        )}
    </div>
  );
}

export default RightPanel;
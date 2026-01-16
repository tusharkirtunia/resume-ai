const MAX_JOB_LENGTH = 2000;
function LeftPanel({
  flow,
  resume,
  job,
  setJob,
  jobCollapsed,
  setJobCollapsed,
  loading,
  successMsg,
  uiError,
  STEP_LABELS,
  FLOW,
  safeSetFlow,
  scoreVariant,
  setScore,
  setLastScoredAt,
  applyRemovals,
  setLoading
}) {
  return (
    <div style={{ background: "#fff", padding: "1.5rem", borderRadius: "8px" }}>
      <h1>Resume Decision Engine</h1>

      {flow === FLOW.APPLIED && (
        <div
            style={{
            background: "#eef7ff",
            border: "1px solid #cce4ff",
            padding: "0.75rem",
            borderRadius: "6px",
            marginBottom: "1rem",
            fontSize: "0.85rem",
            color: "#003366"
            }}
        >
            This session is complete. The resume has been permanently updated and is now read-only.
        </div>
      )}

      <p
        style={{
            fontSize: "0.9rem",
            color: "#555",
            marginBottom: "0.75rem",
            lineHeight: "1.4"
        }}
      >
        Analyze your resume against a job description and get clear, actionable
        recommendations on which bullet points to keep, review, or remove.
      </p>

      <div
        style={{
            fontSize: "0.75rem",
            color: "#666",
            marginBottom: "1rem",
            lineHeight: "1.4"
        }}
      >
        Your resume and job description are processed only for this session.
        No data is shared externally, and changes are applied only when you
        explicitly confirm.
      </div>
      
      <p><strong>{STEP_LABELS[flow]}</strong></p>

      {uiError && (
        <div
            style={{
                background: "#ffecec",
                color: "#900",
                padding: "0.75rem",
                borderRadius: "6px",
                marginBottom: "1rem",
                fontSize: "0.85rem"
            }}
        >
            {uiError}
        </div>
      )}

      {successMsg && (
        <p style={{ color: "green", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
            {successMsg}
        </p>
      )}

      {loading && <p style={{ color: "#888" }}>Processing…</p>}

      {flow === FLOW.VARIANT_SELECTED && (
        <>
          <h3>Current Resume</h3>
          <pre style={{ background: "#f0f0f0", padding: "1rem" }}>
            {JSON.stringify(resume, null, 2)}
          </pre>

          <h3>Job Description</h3>

          <div
            style={{
                fontSize: "0.75rem",
                color: "#777",
                marginBottom: "0.5rem",
                lineHeight: "1.4"
            }}
          >
            This job description is analyzed locally for this session only.
            It is not stored, uploaded, or shared.
          </div>

          {jobCollapsed ? (
            <>
                <pre
                    style={{
                        background: "#f0f0f0",
                        padding: "1rem",
                        maxHeight: "200px",
                        overflow: "auto",
                        whiteSpace: "pre-wrap",
                        fontSize: "0.85rem"
                    }}
                >
                    {job}
                </pre>

                <button
                    type="button"
                    style={{
                        marginTop: "0.5rem",
                        background: "none",
                        border: "none",
                        color: "#0066cc",
                        fontSize: "0.8rem",
                        cursor: "pointer",
                        padding: 0
                    }}
                    onClick={() => {
                      if (flow === FLOW.APPLIED) return;
                      setJobCollapsed(false);
                    }}
                >
                    Edit job description
                </button>
            </>
            ) : (
                <textarea
                    rows={6}
                    style={{ width: "100%" }}
                    value={job}
                    disabled={loading || flow === FLOW.APPLIED}
                    placeholder="Paste the job description here"
                    onChange={(e) => setJob(e.target.value)}
                />
          )}

          <div
            style={{
                marginTop: "0.25rem",
                fontSize: "0.75rem",
                color: job.length > MAX_JOB_LENGTH ? "#900" : "#777",
                textAlign: "right"
            }}
          >
            {job.length} / {MAX_JOB_LENGTH}
          </div>

          {job.length >= MAX_JOB_LENGTH * 0.85 && job.length <= MAX_JOB_LENGTH && (
            <div
                style={{
                    fontSize: "0.75rem",
                    color: "#b36b00",
                    marginTop: "0.25rem"
                }}
            >
                Approaching maximum length. Consider trimming less relevant sections.
            </div>
          )}

          {job.length > MAX_JOB_LENGTH && (
            <div
                style={{
                    fontSize: "0.75rem",
                    color: "#900",
                    marginTop: "0.25rem"
                }}
            >
                Job description exceeds the maximum allowed length.
            </div>
            )}

          {!job.trim() && (
            <button
                type="button"
                style={{
                    marginTop: "0.5rem",
                    background: "none",
                    border: "none",
                    color: "#0066cc",
                    fontSize: "0.8rem",
                    cursor: "pointer",
                    padding: 0
                }}
                onClick={() =>
                    setJob(
                        "We are looking for a Software Engineer with experience in Python and REST APIs.\n\n" +
                        "Responsibilities:\n" +
                        "- Design and maintain backend services\n" +
                        "- Work with databases and APIs\n\n" +
                        "Requirements:\n" +
                        "- 2+ years of Python experience\n" +
                        "- Familiarity with Flask or FastAPI"
                    )
                }
            >
                Use example job description
            </button>
          )}

          {!job.trim() && (
            <div
                style={{
                    marginTop: "0.5rem",
                    fontSize: "0.8rem",
                    color: "#777",
                    lineHeight: "1.4"
                }}
            >
                Paste the full job description here (responsibilities, requirements,
                skills). The more complete it is, the more accurate the analysis.
            </div>
          )}

          <button
            disabled={
                !job.trim() ||
                job.length > MAX_JOB_LENGTH ||
                flow === FLOW.APPLIED
            }
            onClick={() => safeSetFlow(FLOW.JOB_ENTERED)}
          >
            Confirm Job
          </button>
          
          {!job.trim() && (
            <p style={{ fontSize: "0.8rem", color: "#999" }}>
                Enter a job description to continue
            </p>
          )}
        </>
      )}

      {flow === FLOW.JOB_ENTERED && (
        <>
            <button disabled={loading || flow === FLOW.APPLIED}
                onClick={async () => {
                    setLoading(true);
                    try {
                        const result = await scoreVariant(job);
                        setScore(result);
                        setLastScoredAt(new Date().toLocaleTimeString());
                        safeSetFlow(FLOW.SCORED);
                    } finally {
                        setLoading(false);
                    }
                }}
            >
                {loading ? "Scoring…" : "Score Resume"}
            </button>

          {loading && flow !== FLOW.JOB_ENTERED && (
            <p style={{ color: "#888" }}>Processing…</p>
          )}
        </>
      )}

      {flow === FLOW.READY_TO_APPLY && (
        <>
          <button
            disabled={flow === FLOW.APPLIED}
            onClick={() => applyRemovals(job, { dryRun: true })}
          >
            Dry Run
          </button>
          <br /><br />
          <button
            disabled={loading}
            onClick={async () => {
                const ok = window.confirm(
                    "This will permanently modify the resume. This action cannot be undone. Continue?"
                );
                if (!ok) return;

                setLoading(true);
                try {
                    await applyRemovals(job, { confirm: true });
                    safeSetFlow(FLOW.APPLIED);
                } finally {
                    setLoading(false);
                }
            }}
          >
            {loading ? "Applying…" : "Confirm & Apply"}
          </button>
        </>
      )}
    </div>
  );
}

export default LeftPanel;
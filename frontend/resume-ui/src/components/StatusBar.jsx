export default function StatusBar({ backendStatus, activeVariant, lastScoredAt }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "2rem",
        padding: "0.75rem 1rem",
        background: "#111",
        color: "#eee",
        fontSize: "0.9rem"
      }}
    >
      <span>Backend: {backendStatus.toUpperCase()}</span>
      <span>Variant: {activeVariant || "—"}</span>
      <span>Last Score: {lastScoredAt || "—"}</span>
    </div>
  );
}
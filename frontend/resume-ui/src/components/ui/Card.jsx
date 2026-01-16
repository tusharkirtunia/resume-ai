export default function Card({ children, style }) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: "8px",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        ...style
      }}
    >
      {children}
    </div>
  );
}
export default function Section({ title, children }) {
  return (
    <section style={{ marginBottom: "1.5rem" }}>
      {title && (
        <h3 style={{ marginBottom: "0.75rem" }}>{title}</h3>
      )}
      {children}
    </section>
  );
}
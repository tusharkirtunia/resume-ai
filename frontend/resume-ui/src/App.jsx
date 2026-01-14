import { useEffect, useState } from "react";
import { apiFetch } from "./api";

function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    apiFetch("/")
      .then(() => setStatus("Backend connected"))
      .catch(() => setStatus("Backend unreachable"));
  }, []);

  return (
    <div style={{ padding: "24px", fontFamily: "sans-serif" }}>
      <h1>Resume Decision Engine</h1>
      <p>Status: {status}</p>
    </div>
  );
}

export default App;
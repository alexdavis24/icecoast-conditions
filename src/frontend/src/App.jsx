import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      try {
        const response = await fetch("/api/conditions");
        if (!response.ok) {
          throw new Error("Request failed");
        }
        const data = await response.json();
        if (active) {
          setStatus(`${data.region}: ${data.summary}`);
        }
      } catch {
        if (active) {
          setStatus("Backend is reachable, but the sample feed did not respond.");
        }
      }
    }

    loadStatus();

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Icecoast Conditions</p>
        <h1>Northeast ski scene, in one local app.</h1>
        <p className="lede">
          This is a minimal sample frontend wired to a FastAPI backend running in Docker.
        </p>
        <div className="status">
          <span className="status-label">Current sample status</span>
          <span className="status-value">{status}</span>
        </div>
      </section>
    </main>
  );
}

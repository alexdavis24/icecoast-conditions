import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("Loading...");
  const [messageState, setMessageState] = useState("idle");

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

  async function handleSaveMessage() {
    setMessageState("saving");

    try {
      const response = await fetch("/api/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      setMessageState("saved");
    } catch {
      setMessageState("failed");
    }
  }

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
        <div className="message-panel">
          <button
            className="message-button"
            type="button"
            onClick={handleSaveMessage}
            disabled={messageState === "saving"}
          >
            {messageState === "saving" ? "Saving..." : "Save dummy message"}
          </button>
          <p className={`message-feedback message-feedback-${messageState}`}>
            {messageState === "saved"
              ? "Dummy message saved to Postgres."
              : messageState === "failed"
                ? "Could not save the dummy message."
                : "Click the button to write one dummy row into the database."}
          </p>
        </div>
      </section>
    </main>
  );
}

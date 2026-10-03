import { useEffect, useState, useCallback } from "react";
import "./App.css";

const HOST = "http://127.0.0.1:8000";
const API = `${HOST}/api`;
const NEXT_STATUS = { OPEN: "ACKNOWLEDGED", ACKNOWLEDGED: "RESOLVED" };

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (type) params.append("incident_type", type);
      if (status) params.append("status", status);
      const res = await fetch(`${API}/incidents?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setIncidents(await res.json());
      setError("");
    } catch (e) {
      setError("API se connect nahi ho paa raha: " + e.message);
    }
  }, [type, status]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  const updateStatus = async (id, newStatus) => {
    await fetch(`${API}/incidents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    load();
  };

  const open = incidents.filter((i) => i.status === "OPEN").length;

  return (
    <div className="app">
      <h1>🛡️ VisionGuard Dashboard</h1>

      <div className="stats">
        <div className="card">Total: <b>{incidents.length}</b></div>
        <div className="card">Open: <b>{open}</b></div>
      </div>

      <div className="filters">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">All types</option>
          <option value="restricted_zone">Restricted zone</option>
          <option value="fall_detected">Fall detected</option>
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All status</option>
          <option value="OPEN">OPEN</option>
          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
          <option value="RESOLVED">RESOLVED</option>
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Photo</th><th>Time</th><th>Camera</th><th>Type</th>
            <th>Severity</th><th>Confidence</th><th>Status</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((i) => (
            <tr key={i.id}>
              <td>
                {i.evidence_path ? (
                  <img
                    className="thumb"
                    src={`${HOST}/evidence/${i.evidence_path}`}
                    alt="evidence"
                    onClick={() => setPreview(`${HOST}/evidence/${i.evidence_path}`)}
                  />
                ) : "-"}
              </td>
              <td>{new Date(i.timestamp * 1000).toLocaleString()}</td>
              <td>{i.camera_id}</td>
              <td>{i.incident_type}</td>
              <td><span className={`badge ${i.severity}`}>{i.severity}</span></td>
              <td>{(i.confidence * 100).toFixed(0)}%</td>
              <td>{i.status}</td>
              <td>
                {NEXT_STATUS[i.status] ? (
                  <button onClick={() => updateStatus(i.id, NEXT_STATUS[i.status])}>
                    Mark {NEXT_STATUS[i.status]}
                  </button>
                ) : "✔"}
              </td>
            </tr>
          ))}
          {incidents.length === 0 && (
            <tr><td colSpan="8">Koi incident nahi mila</td></tr>
          )}
        </tbody>
      </table>

      {preview && (
        <div className="overlay" onClick={() => setPreview(null)}>
          <img src={preview} alt="preview" />
        </div>
      )}
    </div>
  );
}
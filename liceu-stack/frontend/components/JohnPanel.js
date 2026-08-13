import { useState } from "react";

const PRIORITY_COLOR = {
  critical: "#dc2626",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

export default function JohnPanel({ suggestions = [], onApprove, onReject }) {
  const [reasons, setReasons] = useState({});

  const buttonStyle = {
    background: "#111827",
    color: "#f8fafc",
    border: "1px solid #334155",
    borderRadius: 8,
    padding: "8px 12px",
    cursor: "pointer",
  };

  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>John (Sugestoes IA)</h3>

      {suggestions.length === 0 && <div style={{ opacity: 0.7 }}>Sem sugestoes pendentes.</div>}

      {suggestions.map((s) => (
        <div key={s.id} style={{ borderTop: "1px solid #1e293b", paddingTop: 10, marginTop: 10 }}>
          <div style={{ fontWeight: 600 }}>{s.message}</div>
          <div style={{ marginTop: 4, fontSize: 12, opacity: 0.8 }}>
            Tipo: {s.type} | Prioridade:{" "}
            <strong style={{ color: PRIORITY_COLOR[s.priority] || "#94a3b8" }}>{s.priority}</strong>
          </div>
          <textarea
            placeholder="Motivo da decisao humana"
            value={reasons[s.id] || ""}
            onChange={(e) => setReasons({ ...reasons, [s.id]: e.target.value })}
            style={{
              marginTop: 8,
              width: "100%",
              minHeight: 54,
              borderRadius: 8,
              border: "1px solid #334155",
              background: "#0f172a",
              color: "#e2e8f0",
              padding: 8,
            }}
          />
          <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
            <button style={buttonStyle} onClick={() => onApprove(s.id, reasons[s.id] || "Aprovado pelo Command Center")}>Aprovar</button>
            <button style={buttonStyle} onClick={() => onReject(s.id, reasons[s.id] || "Rejeitado pelo Command Center")}>Rejeitar</button>
          </div>
        </div>
      ))}
    </section>
  );
}

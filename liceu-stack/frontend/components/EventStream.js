export default function EventStream({ events = [] }) {
  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h2 style={{ marginTop: 0 }}>Event Stream</h2>
      <div style={{ maxHeight: 220, overflow: "auto" }}>
        {events.length === 0 && <div style={{ opacity: 0.7 }}>Sem eventos recentes.</div>}
        {events.map((e) => (
          <div key={e.id} style={{ padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
            <strong>{e.type}</strong> <span style={{ opacity: 0.7 }}>({e.source})</span>
            <div style={{ fontSize: 12, opacity: 0.7 }}>{e.timestamp}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

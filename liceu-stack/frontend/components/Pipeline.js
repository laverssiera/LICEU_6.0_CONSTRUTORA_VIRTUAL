export default function Pipeline({ items = [] }) {
  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>Governanca</h3>
      {items.map((item) => (
        <div key={item.id} style={{ padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
          <div style={{ fontWeight: 600 }}>{item.title}</div>
          <div style={{ fontSize: 12, opacity: 0.75 }}>{item.program} • {item.stage}</div>
        </div>
      ))}
      {items.length === 0 && <div style={{ opacity: 0.7 }}>Sem pipeline ativo.</div>}
    </section>
  );
}

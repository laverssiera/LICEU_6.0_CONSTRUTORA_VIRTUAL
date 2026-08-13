export default function KPIBox({ title, value, accent = "#06b6d4" }) {
  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f172a, #111827)",
        color: "#e2e8f0",
        padding: 20,
        borderRadius: 14,
        border: `1px solid ${accent}`,
        minWidth: 180,
      }}
    >
      <div style={{ fontSize: 13, opacity: 0.8, marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>{value ?? "-"}</div>
    </div>
  );
}

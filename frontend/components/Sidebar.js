export default function Sidebar() {
  return (
    <aside
      style={{
        width: 250,
        background: "#1c1c1c",
        padding: 20,
        minHeight: "100vh",
      }}
    >
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
        <li>Dashboard</li>
        <li>Obras</li>
        <li>Financeiro</li>
        <li>P&D</li>
        <li>ANCHOR</li>
        <li>John AI</li>
      </ul>
    </aside>
  );
}

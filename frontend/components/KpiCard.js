export default function KpiCard({ label, value, signal }) {
  const signalClass = signal === "ok" ? "signal-ok" : signal === "warn" ? "signal-warn" : signal === "risk" ? "signal-risk" : "";

  return (
    <article className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${signalClass}`}>{value}</div>
    </article>
  );
}

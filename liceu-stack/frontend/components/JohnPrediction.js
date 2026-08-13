export default function JohnPrediction({ data, onApprove, isLoading }) {
  if (isLoading) {
    return (
      <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
        <h3 style={{ marginTop: 0 }}>John - Previsao</h3>
        <div style={{ opacity: 0.7 }}>Carregando previsao...</div>
      </section>
    );
  }

  if (!data) {
    return (
      <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
        <h3 style={{ marginTop: 0 }}>John - Previsao</h3>
        <div style={{ opacity: 0.7 }}>Sem previsao disponivel.</div>
      </section>
    );
  }

  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>John - Previsao</h3>
      <div>Atraso previsto: <strong>{Number(data.delay_risk || 0).toFixed(1)}%</strong></div>
      <div>Custo estimado: <strong>R$ {Number(data.estimated_cost || 0).toLocaleString("pt-BR")}</strong></div>
      <div>Risco operacional: <strong>{Number(data.risk_score || 0).toFixed(1)}</strong></div>

      <div style={{ marginTop: 10 }}>Melhor acao:</div>
      <strong>{data.best_action}</strong>

      <div style={{ marginTop: 10, opacity: 0.9 }}>{data.message}</div>

      <div style={{ marginTop: 12 }}>
        {Array.isArray(data.scenarios) && data.scenarios.map((s) => (
          <div key={s.name} style={{ padding: "6px 0", borderTop: "1px solid #1e293b" }}>
            {s.name} - atraso {s.delay}% - custo idx {s.cost}
          </div>
        ))}
      </div>

      {data.status === "pending" && (
        <button
          style={{
            marginTop: 12,
            background: "#111827",
            color: "#f8fafc",
            border: "1px solid #334155",
            borderRadius: 10,
            padding: "10px 14px",
            cursor: "pointer",
          }}
          onClick={onApprove}
        >
          Aprovar decisao
        </button>
      )}
    </section>
  );
}

export default function PortfolioJohn({ data, onApprove, onReject, isLoading }) {
  if (isLoading) {
    return (
      <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
        <h3 style={{ marginTop: 0 }}>John - Portfolio</h3>
        <div style={{ opacity: 0.7 }}>Carregando estrategia de portfolio...</div>
      </section>
    );
  }

  if (!data) {
    return (
      <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
        <h3 style={{ marginTop: 0 }}>John - Portfolio</h3>
        <div style={{ opacity: 0.7 }}>Sem recomendacao de portfolio.</div>
      </section>
    );
  }

  const riskLabel = Number(data.risk || 0) >= 65 ? "Alto" : Number(data.risk || 0) >= 35 ? "Medio" : "Baixo";

  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>John - Portfolio</h3>
      <div>Estrategia sugerida: <strong>{data.strategy}</strong></div>
      <div>ROI esperado: <strong>{Number(data.roi || 0).toFixed(2)}%</strong></div>
      <div>Risco: <strong>{riskLabel}</strong> ({Number(data.risk || 0).toFixed(1)})</div>
      <div>Liquidez: <strong>R$ {Number(data.liquidity || 0).toLocaleString("pt-BR")}</strong></div>
      <div>Diversificacao: <strong>{Number(data.diversification || 0).toFixed(1)}%</strong></div>

      <div style={{ marginTop: 10, fontWeight: 600 }}>Alocacao:</div>
      {(data.allocation || []).map((item) => (
        <div key={`${item.project_id}-${item.allocated}`} style={{ padding: "6px 0", borderTop: "1px solid #1e293b" }}>
          {item.project_name || item.project_external_id} - R$ {Number(item.allocated || 0).toLocaleString("pt-BR")}
        </div>
      ))}

      {(data.alerts || []).length > 0 && (
        <div style={{ marginTop: 10 }}>
          {(data.alerts || []).map((alert) => (
            <div key={alert} style={{ color: "#f59e0b", paddingTop: 4 }}>- {alert}</div>
          ))}
        </div>
      )}

      {data.status === "pending" && (
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button
            style={{
              background: "#111827",
              color: "#f8fafc",
              border: "1px solid #334155",
              borderRadius: 10,
              padding: "10px 14px",
              cursor: "pointer",
            }}
            onClick={onApprove}
          >
            Aprovar estrategia
          </button>
          <button
            style={{
              background: "#111827",
              color: "#f8fafc",
              border: "1px solid #334155",
              borderRadius: 10,
              padding: "10px 14px",
              cursor: "pointer",
            }}
            onClick={onReject}
          >
            Rejeitar estrategia
          </button>
        </div>
      )}
    </section>
  );
}

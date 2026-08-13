export default function Actions({ onApprove, onPause, onPay, onAudit, onTraining }) {
  const buttonStyle = {
    background: "#111827",
    color: "#f8fafc",
    border: "1px solid #334155",
    borderRadius: 10,
    padding: "10px 14px",
    cursor: "pointer",
  };

  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>Acoes Rapidas</h3>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <button style={buttonStyle} onClick={onApprove}>Aprovar negocio</button>
        <button style={buttonStyle} onClick={onPause}>Pausar obra</button>
        <button style={buttonStyle} onClick={onPay}>Liberar pagamento</button>
        <button style={buttonStyle} onClick={onAudit}>Acionar auditoria</button>
        <button style={buttonStyle} onClick={onTraining}>Iniciar treinamento</button>
      </div>
    </section>
  );
}

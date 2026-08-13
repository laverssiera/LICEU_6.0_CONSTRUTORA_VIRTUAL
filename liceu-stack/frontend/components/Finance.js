export default function Finance({ data = {} }) {
  const dre = data.dre || {};
  const cash = data.cash_flow || {};
  return (
    <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
      <h3 style={{ marginTop: 0 }}>Financeiro</h3>
      <div>Receita: {dre.revenue ?? 0}</div>
      <div>Custo: {dre.cost ?? 0}</div>
      <div>Despesas: {dre.expenses ?? 0}</div>
      <div>Inflow: {cash.inflow ?? 0}</div>
      <div>Outflow: {cash.outflow ?? 0}</div>
      <div>ROI: {data.roi ?? 0}</div>
    </section>
  );
}

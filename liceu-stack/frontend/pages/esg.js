import PublicLayout from "../components/PublicLayout";

export default function Esg() {
  return (
    <PublicLayout title="ESG" subtitle="Governanca, impacto e rastreabilidade no ciclo completo da construcao.">
      <section style={boxStyle}>
        <ul style={{ paddingLeft: 18, margin: 0 }}>
          <li>Monitoramento de conformidade e risco operacional</li>
          <li>Rastreio de decisoes com aprovacao humana obrigatoria</li>
          <li>Indicadores sociais e ambientais por obra e portfolio</li>
        </ul>
      </section>
    </PublicLayout>
  );
}

const boxStyle = {
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 14,
  background: "rgba(15,23,42,0.92)",
};

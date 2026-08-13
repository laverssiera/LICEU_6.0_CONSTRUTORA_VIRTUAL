import LeadForm from "../components/LeadForm";
import PublicLayout from "../components/PublicLayout";

export default function Carreiras() {
  return (
    <PublicLayout title="Carreiras" subtitle="Construa carreira em engenharia, dados e operacao integrada.">
      <section style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
        <div style={boxStyle}>
          <h3 style={{ marginTop: 0 }}>Areas em foco</h3>
          <ul style={{ paddingLeft: 18 }}>
            <li>Operacoes de obra e planejamento</li>
            <li>Financeiro e portfolio de engenharia</li>
            <li>Dados, IA e automacao industrial</li>
          </ul>
        </div>
        <LeadForm modulePath="/workspace" intent="Quero participar do time LICEU" />
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

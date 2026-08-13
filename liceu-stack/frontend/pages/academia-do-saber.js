import LeadForm from "../components/LeadForm";
import PublicLayout from "../components/PublicLayout";

export default function AcademiaDoSaber() {
  return (
    <PublicLayout title="Academia do Saber" subtitle="Capacitacao continua para elevar padrao tecnico e decisao operacional.">
      <section style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
        <div style={boxStyle}>
          <h3 style={{ marginTop: 0 }}>Trilhas</h3>
          <ul style={{ paddingLeft: 18 }}>
            <li>Governanca de obra e seguranca</li>
            <li>Planejamento financeiro e portfolio</li>
            <li>IA aplicada para engenharia e manutencao</li>
          </ul>
        </div>
        <LeadForm modulePath="/workspace/pd" intent="Quero entrar na Academia do Saber" />
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

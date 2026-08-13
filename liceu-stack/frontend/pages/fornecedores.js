import LeadForm from "../components/LeadForm";
import PublicLayout from "../components/PublicLayout";

export default function Fornecedores() {
  return (
    <PublicLayout title="Fornecedores" subtitle="Conecte sua capacidade ao ecossistema de obras da LICEU.">
      <section style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
        <div style={boxStyle}>
          <h3 style={{ marginTop: 0 }}>Programa de Integracao</h3>
          <p style={{ color: "#cbd5e1" }}>Cadastro de especialidades, certificacoes, SLA e historico de entregas.</p>
          <ul style={{ paddingLeft: 18 }}>
            <li>Match com obras ativas</li>
            <li>Roteiro de homologacao</li>
            <li>Painel de desempenho por contrato</li>
          </ul>
        </div>
        <LeadForm modulePath="/workspace/fornecedores" intent="Quero fornecer para a LICEU" />
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

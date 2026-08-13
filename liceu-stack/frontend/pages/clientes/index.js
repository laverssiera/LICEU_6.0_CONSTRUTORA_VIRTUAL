import Link from "next/link";

import PublicLayout from "../../components/PublicLayout";

const JOURNEYS = [
  { name: "Construir", href: "/clientes/arquimedes", description: "Fluxo completo de obra, ativo e gestao imobiliaria." },
  { name: "Investir", href: "/clientes/cea", description: "Funding, capital e retorno para engenharia." },
  { name: "Analisar dados", href: "/clientes/cefeida", description: "Analytics, previsao e inteligencia operacional." },
  { name: "Ensaios / qualidade", href: "/clientes/pd", description: "Qualidade, auditoria e padronizacao." },
  { name: "Manutencao", href: "/clientes/anchor", description: "Inspecao, laudos e manutencao preditiva." },
];

export default function Clientes() {
  return (
    <PublicLayout title="Clientes" subtitle="Escolha sua necessidade e entre no modulo ideal.">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
        {JOURNEYS.map((journey) => (
          <Link key={journey.href} href={journey.href} style={cardStyle}>
            <h3 style={{ marginTop: 0 }}>{journey.name}</h3>
            <p style={{ marginBottom: 0, color: "#cbd5e1" }}>{journey.description}</p>
          </Link>
        ))}
      </div>
    </PublicLayout>
  );
}

const cardStyle = {
  textDecoration: "none",
  color: "#f8fafc",
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 14,
  background: "rgba(15,23,42,0.9)",
};

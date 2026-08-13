import Link from "next/link";

import LeadForm from "../components/LeadForm";
import PublicLayout from "../components/PublicLayout";

const MODULES = [
  { name: "Arquimedes", href: "/clientes/arquimedes", detail: "Construa, compre e gerencie ativos imobiliarios" },
  { name: "CEA Investimentos", href: "/clientes/cea", detail: "Inteligencia financeira para engenharia" },
  { name: "CEFEIDA Dados", href: "/clientes/cefeida", detail: "Dados que transformam decisoes" },
  { name: "ANCHOR", href: "/clientes/anchor", detail: "Manutencao inteligente e preditiva" },
  { name: "P&D Liceu", href: "/clientes/pd", detail: "Qualidade, processos e inovacao continua" },
];

export default function Home() {
  return (
    <PublicLayout
      title="LICEU 6.0"
      subtitle="O sistema operacional da construcao civil. Site vende, plataforma executa."
    >
      <section style={heroStyle}>
        <div>
          <h2 style={{ marginTop: 0, fontSize: "clamp(1.6rem, 2.8vw, 2.4rem)" }}>Ecossistema completo para engenharia, capital e operacao</h2>
          <p style={{ color: "#cbd5e1" }}>
            Da aquisicao de clientes a gestao de portfolio no workspace interno. Jornadas claras para cliente,
            fornecedor, talentos e parceiros.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link href="/acessar-plataforma" style={ctaPrimary}>Acessar Plataforma</Link>
            <Link href="/clientes" style={ctaGhost}>Explorar Jornadas</Link>
          </div>
        </div>
        <LeadForm modulePath="/workspace" intent="Quero entrar no ecossistema LICEU" />
      </section>

      <section style={gridStyle}>
        <Card title="Clientes" text="Construcao, investimento, analytics e qualidade com entrada orientada por jornada." href="/clientes" />
        <Card title="Fornecedores" text="Cadastre capacidade, certificacoes e conecte com obras ativas." href="/fornecedores" />
        <Card title="Carreiras" text="Talentos para operar obras, dados, financiamentos e inovacao." href="/carreiras" />
      </section>

      <section style={{ marginTop: 28 }}>
        <h3>Modulos do Ecossistema</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          {MODULES.map((module) => (
            <Link key={module.href} href={module.href} style={moduleCardStyle}>
              <strong>{module.name}</strong>
              <div style={{ marginTop: 6, color: "#cbd5e1", fontSize: 14 }}>{module.detail}</div>
            </Link>
          ))}
        </div>
      </section>

      <section style={{ marginTop: 30, display: "grid", gap: 10 }}>
        <h3 style={{ marginBottom: 0 }}>Prova de Autoridade</h3>
        <div style={proofStyle}>+15 pilares conectados, governanca de decisao assistida e acao humana auditavel.</div>
        <div style={proofStyle}>John IA com previsao, simulacao, portfolio e aprovacao obrigatoria no Command Center.</div>
      </section>
    </PublicLayout>
  );
}

function Card({ title, text, href }) {
  return (
    <Link href={href} style={cardStyle}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <p style={{ marginBottom: 0, color: "#cbd5e1" }}>{text}</p>
    </Link>
  );
}

const heroStyle = {
  display: "grid",
  gridTemplateColumns: "1.6fr 1fr",
  gap: 14,
  alignItems: "stretch",
  background: "rgba(2, 6, 23, 0.5)",
  border: "1px solid #1e293b",
  borderRadius: 18,
  padding: 18,
};

const gridStyle = {
  marginTop: 24,
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
};

const cardStyle = {
  textDecoration: "none",
  color: "#f8fafc",
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 14,
  background: "linear-gradient(160deg, rgba(15,23,42,0.95), rgba(12,74,110,0.5))",
};

const moduleCardStyle = {
  textDecoration: "none",
  color: "#f8fafc",
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 12,
  background: "rgba(15,23,42,0.92)",
};

const ctaPrimary = {
  textDecoration: "none",
  color: "#f8fafc",
  background: "linear-gradient(90deg, #0369a1, #0ea5e9)",
  border: "1px solid #0ea5e9",
  borderRadius: 10,
  padding: "10px 14px",
  fontWeight: 700,
};

const ctaGhost = {
  textDecoration: "none",
  color: "#bae6fd",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "10px 14px",
};

const proofStyle = {
  border: "1px solid #1e293b",
  borderRadius: 12,
  padding: 12,
  background: "rgba(15,23,42,0.86)",
};

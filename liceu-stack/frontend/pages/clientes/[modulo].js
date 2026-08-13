import Link from "next/link";
import { useRouter } from "next/router";

import LeadForm from "../../components/LeadForm";
import PublicLayout from "../../components/PublicLayout";

const MODULES = {
  arquimedes: {
    title: "Arquimedes",
    headline: "Construa, compre e gerencie ativos imobiliarios",
    bullets: ["Compra e venda", "Gestao de imoveis", "Integracao com obras"],
    modulePath: "/workspace/arquimedes",
    intent: "Quero investir / Quero construir",
  },
  cea: {
    title: "CEA Investimentos",
    headline: "Inteligencia financeira para engenharia",
    bullets: ["Funding de obras", "Gestao de capital", "Analise de retorno"],
    modulePath: "/workspace/hub",
    intent: "Quero investir / Quero captar recursos",
  },
  cefeida: {
    title: "CEFEIDA Dados",
    headline: "Dados que transformam decisoes",
    bullets: ["Analytics", "Previsoes", "Inteligencia operacional"],
    modulePath: "/workspace/john",
    intent: "Quero previsao e inteligencia operacional",
  },
  anchor: {
    title: "ANCHOR",
    headline: "Manutencao inteligente e preditiva",
    bullets: ["Inspecoes", "Laudos", "Monitoramento"],
    modulePath: "/workspace/anchor",
    intent: "Quero manutencao inteligente",
  },
  pd: {
    title: "P&D Liceu",
    headline: "Qualidade, processos e inovacao continua",
    bullets: ["Ensaios laboratoriais", "Melhoria de processos", "Padronizacao"],
    modulePath: "/workspace/pd",
    intent: "Quero elevar qualidade e processos",
  },
};

export default function ModuloCliente() {
  const router = useRouter();
  const modulo = String(router.query.modulo || "");
  const data = MODULES[modulo] || MODULES.arquimedes;

  return (
    <PublicLayout title={data.title} subtitle={data.headline}>
      <section style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
        <div style={{ border: "1px solid #334155", borderRadius: 14, padding: 14, background: "rgba(15,23,42,0.92)" }}>
          <h3 style={{ marginTop: 0 }}>O que voce ganha</h3>
          <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
            {data.bullets.map((item) => (
              <li key={item} style={{ marginBottom: 8 }}>{item}</li>
            ))}
          </ul>

          <Link href={data.modulePath} style={{ display: "inline-block", marginTop: 14, textDecoration: "none", color: "#f8fafc", border: "1px solid #0ea5e9", background: "linear-gradient(90deg, #0369a1, #0ea5e9)", borderRadius: 10, padding: "10px 14px", fontWeight: 700 }}>
            Ir para {data.title}
          </Link>
        </div>

        <LeadForm modulePath={data.modulePath} intent={data.intent} />
      </section>
    </PublicLayout>
  );
}

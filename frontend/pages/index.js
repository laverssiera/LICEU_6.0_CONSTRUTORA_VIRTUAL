import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import Card from "../components/Card";

export default function Home() {
  return (
    <div className="site-shell">
      <Navbar />
      <Hero />

      <section className="section">
        <h2 className="section-title">O ecossistema que opera de ponta a ponta</h2>
        <p className="section-subtitle">Plataforma institucional e operacional orientada por dados, execucao e capital.</p>

        <div className="card-grid">
          <Card title="Obras Pesadas" desc="Infraestrutura critica com monitoramento tecnico-financeiro." />
          <Card title="Obras Comuns" desc="Escala, produtividade e controle de risco em tempo real." />
          <Card title="Servicos" desc="Portfolio resiliente para capturar oportunidades em ciclos de crise." />
          <Card title="Econotech" desc="Macroeconomia aplicada para antecipar movimentos de mercado." />
        </div>
      </section>

      <section className="section" style={{ paddingTop: 8 }}>
        <h2 className="section-title">Decisao com lastro tecnico</h2>
        <div className="card-grid">
          <Card title="Command Center" desc="KPIs globais, alertas, eventos e recomendacoes do John." />
          <Card title="Investimentos" desc="Alocacao dinamica em cenarios macro e risco ajustado." />
          <Card title="Bolsa LEX" desc="Preco justo reagindo a dados reais de mercado e economia." />
          <Card title="Trust Layer" desc="Compliance, auditoria encadeada e score de saude empresarial." />
        </div>
      </section>
    </div>
  );
}

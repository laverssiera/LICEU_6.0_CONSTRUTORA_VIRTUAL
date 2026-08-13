import Navbar from "../components/Navbar";
import Card from "../components/Card";

export default function Investidores() {
  return (
    <div className="site-shell">
      <Navbar />

      <section className="hero" style={{ minHeight: "56vh" }}>
        <div className="hero-content">
          <p className="hero-kicker">Capital Intelligence</p>
          <h1 className="hero-title">Infraestrutura, dados e capital com leitura macro em tempo real.</h1>
          <p className="hero-subtitle">Gestao de exposicao, risco e precificacao com suporte de Quant, LEX e Econotech.</p>
          <button className="btn-primary">Quero investir</button>
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">Painel do investidor</h2>
        <div className="card-grid">
          <Card title="Pressao Economica" desc="Monitoramento continuo de inflacao, juros e commodities." />
          <Card title="Risco por Projeto" desc="Score economico e recomendacao de exposicao por ativo." />
          <Card title="Liquidez LEX" desc="Preco justo e reacao do mercado para ativos tokenizados." />
        </div>
      </section>
    </div>
  );
}

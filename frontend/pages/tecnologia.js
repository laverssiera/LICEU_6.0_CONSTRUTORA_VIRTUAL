import Navbar from "../components/Navbar";
import Card from "../components/Card";

export default function Tecnologia() {
  return (
    <div className="site-shell">
      <Navbar />

      <section className="section">
        <h1 className="section-title">Tecnologia LICEU 6.0</h1>
        <p className="section-subtitle">Arquitetura para operar construcao, mercado e capital em uma unica espinha digital.</p>

        <div className="card-grid">
          <Card title="John Core" desc="Inteligencia operacional para sintese, recomendacao e governanca de decisao." />
          <Card title="Econotech" desc="Analise macroeconomica para precificacao, risco e alocacao de recursos." />
          <Card title="Core-DNA Events" desc="Eventos padronizados para rastreabilidade ponta a ponta." />
          <Card title="Trust Layer" desc="Compliance e score de saude para operacoes de alta responsabilidade." />
        </div>
      </section>
    </div>
  );
}
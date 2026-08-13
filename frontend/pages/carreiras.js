import Navbar from "../components/Navbar";

export default function Carreiras() {
  return (
    <div className="site-shell">
      <Navbar />
      <section className="section">
        <h1 className="section-title">Carreiras</h1>
        <p className="section-subtitle">Trilhas para engenharia, operacao, dados, produto e P&D.</p>
        <button className="btn-primary">Ver vagas</button>
      </section>
    </div>
  );
}

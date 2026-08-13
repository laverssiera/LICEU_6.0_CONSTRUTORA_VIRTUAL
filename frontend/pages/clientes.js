import Navbar from "../components/Navbar";
import Journey from "../components/Journey";

export default function Clientes() {
  return (
    <div className="site-shell">
      <Navbar />
      <section className="section">
        <h1 className="section-title">Clientes</h1>
        <p className="section-subtitle">Fluxos completos para quem precisa construir, investir e escalar com previsibilidade.</p>

        <Journey title="Construir" />
        <Journey title="Investir" />
        <Journey title="Analisar dados" />
        <Journey title="Qualidade" />
      </section>
    </div>
  );
}

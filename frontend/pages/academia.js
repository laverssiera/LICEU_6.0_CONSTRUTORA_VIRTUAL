import Navbar from "../components/Navbar";

export default function Academia() {
  return (
    <div className="site-shell">
      <Navbar />
      <section className="section">
        <h1 className="section-title">Academia</h1>
        <p className="section-subtitle">Cursos e certificacoes para o ecossistema tecnico-operacional da LICEU.</p>
        <button className="btn-primary">Explorar cursos</button>
      </section>
    </div>
  );
}

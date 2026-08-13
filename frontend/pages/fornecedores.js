import Navbar from "../components/Navbar";

export default function Fornecedores() {
  return (
    <div className="site-shell">
      <Navbar />
      <section className="section">
        <h1 className="section-title">Fornecedores</h1>
        <p className="section-subtitle">Pedidos, contratos, capacidade e risco operacional em um fluxo unico.</p>
        <button className="btn-primary">Entrar como fornecedor</button>
      </section>
    </div>
  );
}

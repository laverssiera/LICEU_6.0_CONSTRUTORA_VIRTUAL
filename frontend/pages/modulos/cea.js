import Navbar from "../../components/Navbar";
import LeadForm from "../../components/LeadForm";

export default function CEA() {
  return (
    <div>
      <Navbar />
      <div className="section-white">
        <h1>CEA</h1>
        <p>Gestao financeira, DRE e fluxo de caixa para operacao e investimento.</p>
        <LeadForm />
        <button className="btn-primary">Acessar CEA</button>
      </div>
    </div>
  );
}

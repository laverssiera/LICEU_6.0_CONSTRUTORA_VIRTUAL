import Navbar from "../../components/Navbar";
import LeadForm from "../../components/LeadForm";

export default function Cefeida() {
  return (
    <div>
      <Navbar />
      <div className="section-white">
        <h1>Cefeida</h1>
        <p>Camada estrategica para simulacoes, indicadores macro e priorizacao de portfolio.</p>
        <LeadForm />
        <button className="btn-primary">Acessar Cefeida</button>
      </div>
    </div>
  );
}

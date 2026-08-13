import Navbar from "../../components/Navbar";
import LeadForm from "../../components/LeadForm";

export default function Anchor() {
  return (
    <div>
      <Navbar />
      <div className="section-white">
        <h1>Anchor</h1>
        <p>Padronizacao de qualidade, auditorias e controle de nao conformidades.</p>
        <LeadForm />
        <button className="btn-primary">Acessar Anchor</button>
      </div>
    </div>
  );
}

import Navbar from "../../components/Navbar";
import LeadForm from "../../components/LeadForm";

export default function Arquimedes() {
  return (
    <div>
      <Navbar />
      <div className="section-white">
        <h1>Arquimedes</h1>

        <p>Plataforma imobiliaria integrada ao ecossistema.</p>

        <LeadForm />

        <button className="btn-primary">Acessar Arquimedes</button>
      </div>
    </div>
  );
}

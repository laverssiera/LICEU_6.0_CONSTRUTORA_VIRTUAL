import Navbar from "../../components/Navbar";
import LeadForm from "../../components/LeadForm";
import PDProcessStudio from "../../components/PDProcessStudio";

export default function PD() {
  return (
    <div>
      <Navbar />
      <div className="section-white">
        <h1>P&D</h1>
        <p>Pesquisa e desenvolvimento com experimentacao, aprendizado e melhoria continua.</p>
        <div className="pd-page-lead">
          <LeadForm />
        </div>
        <PDProcessStudio />
      </div>
    </div>
  );
}

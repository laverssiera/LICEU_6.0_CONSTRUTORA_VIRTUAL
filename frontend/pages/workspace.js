import AppLayout from "../components/AppLayout";
import EconotechSimulator from "../components/EconotechSimulator";
import KpiCard from "../components/KpiCard";
import PDProcessStudio from "../components/PDProcessStudio";
import StressDashboard from "../components/StressDashboard";
import UniversalCommandCenter from "../components/UniversalCommandCenter";

export default function Workspace() {
  const kpis = [
    { label: "Receita consolidada", value: "R$ 412M", delta: "+8.2%" },
    { label: "Margem operacional", value: "21.4%", delta: "+1.1 p.p" },
    { label: "Pressao economica", value: "0.63", delta: "-0.04" },
    { label: "Score trust", value: "93/100", delta: "+2" },
  ];

  const rows = [
    ["Obra Norte", "SP", "Em execucao", "0.57", "Ajustar hedge"],
    ["Complexo Delta", "BA", "Planejamento", "0.71", "Revisar capex"],
    ["Linha Verde", "PR", "Entrega", "0.48", "Manter ritmo"],
    ["Hub Rio", "RJ", "Escopo", "0.66", "Renegociar insumos"],
  ];

  return (
    <AppLayout>
      <div className="workspace-grid">
        <section className="panel panel-main">
          <h1 className="panel-title">Command Center</h1>
          <p className="panel-subtitle">Visao consolidada de operacao, risco e mercado.</p>

          <div className="kpi-grid">
            {kpis.map((item) => (
              <KpiCard key={item.label} label={item.label} value={item.value} delta={item.delta} />
            ))}
          </div>

          <div className="table-card">
            <div className="table-title">Radar de projetos</div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Projeto</th>
                  <th>UF</th>
                  <th>Fase</th>
                  <th>Risco econ.</th>
                  <th>Acao sugerida</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row[0]}>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td>{row[3]}</td>
                    <td>{row[4]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <EconotechSimulator />
          <UniversalCommandCenter />
          <PDProcessStudio />
          <StressDashboard />
        </section>

        <aside className="panel panel-side">
          <h2 className="panel-title">Sinais do John</h2>
          <div className="signal-list">
            <div className="signal-item">
              <strong>Risco de insumos</strong>
              <p>Commodity em alta. Recomendada revisao de contratos longos.</p>
            </div>
            <div className="signal-item">
              <strong>Juros e financiamento</strong>
              <p>Curva curta estabilizando. Janela favoravel para repricing.</p>
            </div>
            <div className="signal-item">
              <strong>Liquidez LEX</strong>
              <p>Ativos logisticos com spread menor e melhor demanda.</p>
            </div>
          </div>
        </aside>
      </div>
    </AppLayout>
  );
}

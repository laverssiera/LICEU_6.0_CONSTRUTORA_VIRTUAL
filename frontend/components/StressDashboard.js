import { useEffect, useState } from "react";

const FALLBACK = {
  system_risk: "HIGH",
  system_mode: "CRISE",
  projects_critical: 5,
  contagion_rate: 0.42,
  capital_loss_estimate: 12000000,
  recommended_action: "DEFENSIVE_MODE",
  john_crisis_mode: {
    recommended_actions: [
      "suspender novos projetos de alto risco",
      "preservar caixa",
      "renegociar contratos criticos",
      "priorizar projetos com fluxo garantido",
    ],
  },
  response_plan: {
    capital: { action: "preserve_cash_and_freeze_risk", reserve_subscription: { subscription: { amount: 600000 } } },
    quant: { actions: [{ project_id: "obra-norte", action: "reduce", reason: "risk_above_threshold" }] },
    lex: { action: "defensive_market_mode", sync: { count: 3 } },
    opera: { action: "pause_high_risk_projects", signals: [{ id: "sig-1" }, { id: "sig-2" }] },
    pd: { action: "activate_emergency_processes" },
    automatic_execution: { executed: true, quant_actions: 1, paused_projects: 2, held_projects: 1, execution_signals: 2, lex_assets_synced: 3 },
  },
};

function currency(value) {
  return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
}

export default function StressDashboard() {
  const [stress, setStress] = useState(FALLBACK);
  const [source, setSource] = useState("fallback local");

  useEffect(() => {
    let active = true;

    async function loadStress() {
      try {
        const response = await fetch("/gateway/econotech/dashboard");
        if (!response.ok) {
          throw new Error(`gateway status ${response.status}`);
        }
        const payload = await response.json();
        const report = payload.result?.stress_test;
        if (!report) {
          throw new Error("stress payload missing");
        }
        if (active) {
          setStress(report);
          setSource("gateway econotech");
        }
      } catch (_error) {
        if (active) {
          setStress(FALLBACK);
          setSource("fallback local");
        }
      }
    }

    loadStress();
    return () => {
      active = false;
    };
  }, []);

  const riskClass = stress.system_risk === "HIGH" ? "signal-risk" : stress.system_risk === "ALERT" ? "signal-warn" : "signal-ok";

  return (
    <section className="panel stress-dashboard">
      <div className="stress-head">
        <div>
          <h2 className="panel-title">Modo Crise</h2>
          <p className="panel-subtitle">Stress test sistêmico com efeito dominó, perda de capital e ações defensivas.</p>
        </div>
        <div className="sim-source">Fonte: {source}</div>
      </div>

      <div className="stress-kpis">
        <article className="stress-kpi">
          <div className="kpi-label">Risco sistêmico</div>
          <div className={`kpi-value ${riskClass}`}>{stress.system_risk}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Projetos críticos</div>
          <div className="kpi-value">{stress.projects_critical}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Contágio</div>
          <div className="kpi-value">{Math.round(Number(stress.contagion_rate || 0) * 100)}%</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Perda estimada</div>
          <div className="kpi-value">{currency(stress.capital_loss_estimate)}</div>
        </article>
      </div>

      <div className="stress-mode-row">
        <strong>Modo do sistema:</strong> {stress.system_mode || "CRISE"} | <strong>Acao:</strong> {stress.recommended_action}
      </div>

      <div className="stress-actions-grid">
        <article className="stress-kpi">
          <div className="kpi-label">Capital</div>
          <div className="stress-action-value">{stress.response_plan?.capital?.action || "n/a"}</div>
          <div className="stress-action-meta">reserva: {currency(stress.response_plan?.capital?.reserve_subscription?.subscription?.amount || 0)}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Quant</div>
          <div className="stress-action-value">{stress.response_plan?.automatic_execution?.quant_actions || 0} acoes</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">LEX</div>
          <div className="stress-action-value">{stress.response_plan?.lex?.action || "n/a"}</div>
          <div className="stress-action-meta">ativos sync: {stress.response_plan?.automatic_execution?.lex_assets_synced || stress.response_plan?.lex?.sync?.count || 0}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">OPERA/P&D</div>
          <div className="stress-action-value">{stress.response_plan?.opera?.action || "n/a"} | {stress.response_plan?.pd?.action || "n/a"}</div>
          <div className="stress-action-meta">sinais: {stress.response_plan?.automatic_execution?.execution_signals || stress.response_plan?.opera?.signals?.length || 0}</div>
        </article>
      </div>

      <div className="signal-list">
        <div className="signal-item">
          Execucao automatica: {stress.response_plan?.automatic_execution?.executed ? "ativa" : "inativa"} | pausados: {stress.response_plan?.automatic_execution?.paused_projects || 0} | hold: {stress.response_plan?.automatic_execution?.held_projects || 0}
        </div>
      </div>

      <div className="signal-list">
        {(stress.john_crisis_mode?.recommended_actions || []).map((item) => (
          <div key={item} className="signal-item">{item}</div>
        ))}
      </div>
    </section>
  );
}
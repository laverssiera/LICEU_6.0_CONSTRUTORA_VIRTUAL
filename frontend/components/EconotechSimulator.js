import { useMemo, useState } from "react";

const INITIAL_DATA = {
  inflation: 5.5,
  interest_rate: 12.75,
  gdp_growth: 2.1,
  steel_price: 100,
  cement_price: 80,
  exchange_rate: 5.1,
  construction_demand: 0.7,
};

function toNumber(value, fallback = 0) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

function economicFactors(data) {
  return {
    cost_pressure: (data.steel_price + data.cement_price) / 2,
    credit_condition: data.interest_rate,
    demand_strength: data.construction_demand,
    growth_momentum: data.gdp_growth,
  };
}

function generateScenarios(factors) {
  return {
    expansion: {
      growth: factors.growth_momentum + 1.5,
      interest: Math.max(0, factors.credit_condition - 2),
      demand: Math.min(1, factors.demand_strength + 0.2),
    },
    stability: {
      growth: factors.growth_momentum,
      interest: factors.credit_condition,
      demand: factors.demand_strength,
    },
    contraction: {
      growth: factors.growth_momentum - 1.5,
      interest: factors.credit_condition + 2,
      demand: Math.max(0, factors.demand_strength - 0.3),
    },
  };
}

function projectImpact(scenario) {
  const cost = scenario.interest * 0.3;
  const demand = scenario.demand * 0.5;
  const growth = scenario.growth * 0.2;
  const viability = demand + growth - cost;

  let risk = "high";
  if (viability >= 0.35) risk = "low";
  else if (viability >= 0) risk = "medium";

  return {
    viability_score: Number(viability.toFixed(4)),
    risk,
  };
}

export default function EconotechSimulator() {
  const [data, setData] = useState(INITIAL_DATA);
  const [forecast, setForecast] = useState(null);
  const [mode, setMode] = useState("local");

  const normalized = useMemo(
    () => ({
      inflation: toNumber(data.inflation, 5.5),
      interest_rate: toNumber(data.interest_rate, 12.75),
      gdp_growth: toNumber(data.gdp_growth, 2.1),
      steel_price: toNumber(data.steel_price, 100),
      cement_price: toNumber(data.cement_price, 80),
      exchange_rate: toNumber(data.exchange_rate, 5.1),
      construction_demand: Math.max(0, Math.min(1, toNumber(data.construction_demand, 0.7))),
    }),
    [data]
  );

  const runLocalSimulation = () => {
    const factors = economicFactors(normalized);
    const scenarios = generateScenarios(factors);

    const result = {
      expansion: projectImpact(scenarios.expansion),
      stability: projectImpact(scenarios.stability),
      contraction: projectImpact(scenarios.contraction),
    };

    const best = Object.keys(result).reduce((acc, key) => {
      return result[key].viability_score > result[acc].viability_score ? key : acc;
    }, "expansion");

    const nextForecast = {
      factors,
      result,
      best,
      alerts: [
        result.contraction.risk === "high" ? "Alerta: cenario de contracao com alto risco de viabilidade." : null,
        normalized.interest_rate > 13 ? "Alerta: juros elevados comprimem margem e credito." : null,
        normalized.construction_demand < 0.5 ? "Alerta: demanda fraca sugere postura defensiva." : null,
      ].filter(Boolean),
    };

    setForecast(nextForecast);
    return nextForecast;
  };

  const runSimulation = async () => {
    try {
      const response = await fetch("/gateway/econotech/scenarios/forecast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: normalized,
          weights: { expansion: 0.25, stability: 0.5, contraction: 0.25 },
          simulations: 200,
        }),
      });

      if (!response.ok) {
        throw new Error(`gateway status ${response.status}`);
      }

      const payload = await response.json();
      const result = payload.result?.forecast || payload.forecast;
      const best = payload.result?.best_scenario || payload.best_scenario;
      const decision = payload.result?.decision || payload.decision;

      if (!result || !best) {
        throw new Error("forecast payload missing fields");
      }

      setMode("gateway");
      setForecast({
        factors: payload.result?.factors || payload.factors,
        result,
        best,
        decision,
        alerts: [
          result.contraction?.risk === "high" ? "Alerta: cenario de contracao com alto risco de viabilidade." : null,
          normalized.interest_rate > 13 ? "Alerta: juros elevados comprimem margem e credito." : null,
        ].filter(Boolean),
      });
    } catch (error) {
      setMode("local");
      runLocalSimulation();
    }
  };

  const setField = (key) => (event) => {
    setData((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const bestScenario = forecast?.best;

  return (
    <section className="panel econotech-simulator">
      <h2 className="panel-title">Econotech - Motor de Cenarios</h2>
      <p className="panel-subtitle">Simular futuros, medir impacto e orientar decisao de investimento e execucao.</p>

      <div className="sim-grid">
        <label>
          Inflacao
          <input value={data.inflation} onChange={setField("inflation")} />
        </label>
        <label>
          Juros
          <input value={data.interest_rate} onChange={setField("interest_rate")} />
        </label>
        <label>
          PIB
          <input value={data.gdp_growth} onChange={setField("gdp_growth")} />
        </label>
        <label>
          Aco
          <input value={data.steel_price} onChange={setField("steel_price")} />
        </label>
        <label>
          Cimento
          <input value={data.cement_price} onChange={setField("cement_price")} />
        </label>
        <label>
          Cambio
          <input value={data.exchange_rate} onChange={setField("exchange_rate")} />
        </label>
        <label>
          Demanda (0-1)
          <input value={data.construction_demand} onChange={setField("construction_demand")} />
        </label>
      </div>

      <button className="btn-primary" onClick={runSimulation}>Rodar cenarios</button>

      {forecast && (
        <div className="sim-result">
          <div className="sim-cards">
            <article className={"sim-card" + (bestScenario === "expansion" ? " is-best" : "")}>
              <h3>Expansao</h3>
              <p>Viabilidade: {forecast.result.expansion.viability_score.toFixed(2)}</p>
              <p>Risco: {forecast.result.expansion.risk}</p>
            </article>
            <article className={"sim-card" + (bestScenario === "stability" ? " is-best" : "")}>
              <h3>Estabilidade</h3>
              <p>Viabilidade: {forecast.result.stability.viability_score.toFixed(2)}</p>
              <p>Risco: {forecast.result.stability.risk}</p>
            </article>
            <article className={"sim-card" + (bestScenario === "contraction" ? " is-best" : "")}>
              <h3>Contracao</h3>
              <p>Viabilidade: {forecast.result.contraction.viability_score.toFixed(2)}</p>
              <p>Risco: {forecast.result.contraction.risk}</p>
            </article>
          </div>

          <div className="sim-decision">
            <div className="sim-source">Fonte: {mode === "gateway" ? "Gateway ECONOTECH" : "Fallback local"}</div>
            <strong>John Economico:</strong> cenario mais favoravel = {forecast.best}
            <p>Recomendacao: priorizar projetos menos sensiveis a juros e evitar alavancagem excessiva.</p>
            {forecast.decision && (
              <p>
                Decisoes: Quant={forecast.decision.quant?.action || "n/a"} | LEX={forecast.decision.lex?.action || "n/a"} | OPERA={forecast.decision.opera?.action || "n/a"}
              </p>
            )}
          </div>

          {forecast.alerts.length > 0 && (
            <div className="sim-alerts">
              {forecast.alerts.map((alert) => (
                <div key={alert} className="signal-item">{alert}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

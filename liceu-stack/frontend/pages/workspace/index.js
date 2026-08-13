import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import Actions from "../../components/Actions";
import EventStream from "../../components/EventStream";
import Finance from "../../components/Finance";
import JohnPanel from "../../components/JohnPanel";
import JohnPrediction from "../../components/JohnPrediction";
import KPIBox from "../../components/KPIBox";
import Pipeline from "../../components/Pipeline";
import PortfolioJohn from "../../components/PortfolioJohn";

const MENU = [
  { key: "dashboard", label: "Dashboard", href: "/workspace" },
  { key: "opera", label: "Obras", href: "/workspace/opera" },
  { key: "hub", label: "Financeiro", href: "/workspace/hub" },
  { key: "fornecedores", label: "Fornecedores", href: "/workspace/fornecedores" },
  { key: "pd", label: "P&D", href: "/workspace/pd" },
  { key: "anchor", label: "ANCHOR", href: "/workspace/anchor" },
  { key: "john", label: "John AI", href: "/workspace/john" },
];

const CIVILIZATION_AREAS = [
  {
    key: "runtime",
    label: "Civilization Runtime",
    description: "Execucao central, orquestracao e ciclo operacional.",
  },
  {
    key: "economy",
    label: "Civilization Economy",
    description: "Fluxos financeiros, alocacao e sustentabilidade.",
  },
  {
    key: "knowledge",
    label: "Civilization Knowledge",
    description: "Memoria, aprendizado e preservacao do contexto.",
  },
  {
    key: "policy",
    label: "Civilization Policy",
    description: "Regras, governanca e validacao de decisoes.",
  },
  {
    key: "planner",
    label: "Civilization Planner",
    description: "Planejamento, sequenciamento e priorizacao.",
  },
  {
    key: "state",
    label: "Civilization State",
    description: "Estado consolidado, snapshot e continuidade.",
  },
];

export default function Workspace({ activeAreaKey = "runtime" } = {}) {
  const API_BASE = "http://localhost:8000";

  const [kpis, setKpis] = useState({});
  const [pipeline, setPipeline] = useState([]);
  const [projects, setProjects] = useState([]);
  const [finance, setFinance] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [events, setEvents] = useState([]);
  const [johnSuggestions, setJohnSuggestions] = useState([]);
  const [johnPrediction, setJohnPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(true);
  const [johnPortfolio, setJohnPortfolio] = useState(null);
  const [loadingPortfolio, setLoadingPortfolio] = useState(true);
  const [result, setResult] = useState(null);
  const activeArea = CIVILIZATION_AREAS.find((area) => area.key === activeAreaKey) || CIVILIZATION_AREAS[0];

  const loadDashboard = async () => {
    const [kpiRes, pipelineRes, projectsRes, financeRes, alertsRes, eventsRes, johnRes] = await Promise.all([
      fetch(`${API_BASE}/dashboard/kpis`),
      fetch(`${API_BASE}/dashboard/pipeline`),
      fetch(`${API_BASE}/dashboard/projects`),
      fetch(`${API_BASE}/dashboard/finance`),
      fetch(`${API_BASE}/dashboard/alerts`),
      fetch(`${API_BASE}/dashboard/events?limit=20`),
      fetch(`${API_BASE}/dashboard/john/suggestions?status=pending&limit=10`),
    ]);

    setKpis(await kpiRes.json());
    setPipeline((await pipelineRes.json()).items || []);
    setProjects((await projectsRes.json()).items || []);
    setFinance(await financeRes.json());
    setAlerts((await alertsRes.json()).items || []);
    setEvents((await eventsRes.json()).items || []);
    setJohnSuggestions((await johnRes.json()).items || []);
  };

  const loadPrediction = async (projectId = null) => {
    setLoadingPrediction(true);
    const query = projectId ? `?project_id=${projectId}` : "";
    const res = await fetch(`${API_BASE}/dashboard/john/prediction${query}`);
    const data = await res.json();
    setJohnPrediction(data.item || null);
    setLoadingPrediction(false);
  };

  const loadPortfolio = async () => {
    setLoadingPortfolio(true);
    const res = await fetch(`${API_BASE}/dashboard/john/portfolio`);
    const data = await res.json();
    setJohnPortfolio(data.item || null);
    setLoadingPortfolio(false);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    loadPrediction(projects[0] ? projects[0].id : null);
  }, [projects]);

  useEffect(() => {
    loadPortfolio();
  }, [projects, finance]);

  const firstBusinessId = useMemo(() => (pipeline[0] ? pipeline[0].id : "business-1"), [pipeline]);
  const firstProjectId = useMemo(() => (projects[0] ? projects[0].id : "project-business-1"), [projects]);
  const civilizationMenu = useMemo(
    () => CIVILIZATION_AREAS.map((area) => ({ ...area, href: `/workspace/${area.key}` })),
    [],
  );

  const callAction = async (path, payload = null) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : null,
    });
    const data = await res.json();
    setResult(data);
    await loadDashboard();
    await loadPortfolio();
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", minHeight: "100vh", background: "#020617", color: "#e2e8f0", fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif" }}>
      <aside style={{ borderRight: "1px solid #1e293b", padding: 16, background: "#0b1220" }}>
        <h2 style={{ marginTop: 0 }}>LICEU</h2>
        <nav style={{ display: "grid", gap: 6 }}>
          {MENU.map((item) => (
            <Link key={item.key} href={item.href} style={{ color: "#cbd5e1", textDecoration: "none", border: "1px solid #1e293b", borderRadius: 8, padding: "8px 10px", background: "#111827" }}>
              {item.label}
            </Link>
          ))}
        </nav>

        <div style={{ marginTop: 18 }}>
          <div style={{ fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 8 }}>
            Civilization Modules
          </div>
          <nav style={{ display: "grid", gap: 6 }}>
            {civilizationMenu.map((item) => (
              <a
                key={item.key}
                href={item.href}
                style={{
                  color: "#cbd5e1",
                  textDecoration: "none",
                  border: "1px solid #1e293b",
                  borderRadius: 8,
                  padding: "8px 10px",
                  background: "#111827",
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
      </aside>

      <main style={{ padding: 18 }}>
        <header style={{ marginBottom: 18, padding: "12px 16px", border: "1px solid #1e293b", borderRadius: 14, background: "#0b1220" }}>
          <h1 style={{ margin: 0 }}>LICEU 6.0 - Civilization Workspace</h1>
          <div style={{ opacity: 0.8, marginTop: 6 }}>
            {activeArea.label} como porta de entrada principal. Runtime + Economy + Knowledge + Policy + Planner + State
          </div>
        </header>

        <section style={{ marginBottom: 14, background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
          <h3 style={{ marginTop: 0 }}>Civilization Domains</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
            {CIVILIZATION_AREAS.map((area) => (
              <article
                key={area.key}
                style={{
                  border: area.key === activeArea.key ? "1px solid #38bdf8" : "1px solid #1e293b",
                  borderRadius: 12,
                  padding: 14,
                  background: area.key === activeArea.key ? "#0f172a" : "#111827",
                }}
              >
                <div style={{ fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 8 }}>
                  {area.key}
                </div>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>{area.label}</div>
                <div style={{ fontSize: 13, lineHeight: 1.5, color: "#94a3b8" }}>{area.description}</div>
              </article>
            ))}
          </div>
        </section>

        <section style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
          <KPIBox title="Receita" value={kpis.revenue} accent="#10b981" />
          <KPIBox title="Projetos" value={kpis.projects} accent="#06b6d4" />
          <KPIBox title="Alertas" value={kpis.alerts} accent="#f97316" />
          <KPIBox title="Health Score" value={kpis.health_score} accent="#a78bfa" />
        </section>

        <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 14 }}>
          <Pipeline items={pipeline} />
          <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
            <h3 style={{ marginTop: 0 }}>Operacoes</h3>
            {projects.map((p) => (
              <div key={p.id} style={{ padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
                <div style={{ fontWeight: 600 }}>{p.name}</div>
                <div style={{ fontSize: 12, opacity: 0.75 }}>
                  Status: {p.status} | Progresso: {p.progress}% | Tasks abertas: {p.tasks_open}
                </div>
              </div>
            ))}
          </section>
          <Finance data={finance} />
        </section>

        <section style={{ marginBottom: 14 }}>
          <EventStream events={events} />
        </section>

        <section style={{ marginBottom: 14 }}>
          <JohnPrediction
            data={johnPrediction}
            isLoading={loadingPrediction}
            onApprove={() =>
              johnPrediction &&
              callAction(`/actions/john-approve-prediction/${johnPrediction.id}`, {
                decision_by: "command_center_user",
                decision_reason: "Aprovado apos simulacao de cenarios",
              })
            }
          />
        </section>

        <section style={{ marginBottom: 14 }}>
          <PortfolioJohn
            data={johnPortfolio}
            isLoading={loadingPortfolio}
            onApprove={() =>
              johnPortfolio &&
              callAction(`/actions/john-approve-portfolio/${johnPortfolio.id}`, {
                decision_by: "command_center_user",
                decision_reason: "Estrategia validada no comite de portfolio",
              })
            }
            onReject={() =>
              johnPortfolio &&
              callAction(`/actions/john-reject-portfolio/${johnPortfolio.id}`, {
                decision_by: "command_center_user",
                decision_reason: "Estrategia rejeitada por risco/capital",
              })
            }
          />
        </section>

        <section style={{ marginBottom: 14 }}>
          <JohnPanel
            suggestions={johnSuggestions}
            onApprove={(id, reason) =>
              callAction(`/actions/john-approve/${id}`, {
                decision_by: "command_center_user",
                decision_reason: reason,
              })
            }
            onReject={(id, reason) =>
              callAction(`/actions/john-reject/${id}`, {
                decision_by: "command_center_user",
                decision_reason: reason,
              })
            }
          />
        </section>

        <section style={{ marginBottom: 14 }}>
          <Actions
            onApprove={() => callAction(`/actions/approve-business/${firstBusinessId}`)}
            onPause={() => callAction(`/actions/pause-project/${firstProjectId}`)}
            onPay={() => callAction(`/actions/release-payment/${firstProjectId}`)}
            onAudit={() => callAction(`/actions/trigger-audit/${firstProjectId}`)}
            onTraining={() => callAction(`/actions/start-training/${firstProjectId}`)}
          />
        </section>

        <section style={{ background: "#0b1220", borderRadius: 14, padding: 18, color: "#cbd5e1" }}>
          <h3 style={{ marginTop: 0 }}>Alertas</h3>
          {alerts.map((a) => (
            <div key={a.id} style={{ padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
              <strong>{a.severity}</strong> - {a.message}
            </div>
          ))}
        </section>

        {result && (
          <pre style={{ marginTop: 14, background: "#0b1220", borderRadius: 14, padding: 14, border: "1px solid #1e293b" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </main>
    </div>
  );
}

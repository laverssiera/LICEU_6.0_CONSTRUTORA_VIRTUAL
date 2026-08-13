import { useEffect, useState } from "react";

const TENANTS = ["tenant_liceu", "tenant_cliente_x", "tenant_investidor_y"];
const ROLES = ["ADMIN", "GESTOR", "OPERADOR", "INVESTIDOR", "CLIENTE", "JOHN"];
const STORAGE_KEY = "liceu.universal.cc.v1";

export default function UniversalCommandCenter() {
  const [tenant, setTenant] = useState("tenant_liceu");
  const [role, setRole] = useState("GESTOR");
  const [status, setStatus] = useState("Pronto para operar o Core Universal.");
  const [loading, setLoading] = useState(false);

  const [projectForm, setProjectForm] = useState({
    portfolio: "Obras Comuns",
    program: "Residencial",
    project: "Projeto Universal",
    project_type: "PRJ",
    year: 2026,
  });

  const [project, setProject] = useState(null);
  const [score, setScore] = useState(null);
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const persisted = JSON.parse(raw);
      if (persisted.tenant && TENANTS.includes(persisted.tenant)) {
        setTenant(persisted.tenant);
      }
      if (persisted.role && ROLES.includes(persisted.role)) {
        setRole(persisted.role);
      }
      if (persisted.projectForm) {
        setProjectForm((prev) => ({ ...prev, ...persisted.projectForm }));
      }
      if (Array.isArray(persisted.history)) {
        setHistory(persisted.history.slice(0, 20));
      }
    } catch (_error) {
      // Fallback silencioso para evitar quebrar render em caso de storage inválido.
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          tenant,
          role,
          projectForm,
          history: history.slice(0, 20),
        }),
      );
    } catch (_error) {
      // Ignora falhas de escrita no storage (quota/permissão).
    }
  }, [tenant, role, projectForm, history]);

  function pushHistory(entry) {
    setHistory((prev) => [entry, ...prev].slice(0, 20));
  }

  function exportHistoryJson() {
    const payload = {
      exported_at: new Date().toISOString(),
      tenant,
      role,
      total: history.length,
      items: history,
    };

    const json = JSON.stringify(payload, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const fileName = `universal-history-${tenant}-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setStatus("Historico exportado em JSON para auditoria operacional.");
  }

  function authHeaders() {
    return {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenant,
      "X-Role": role,
    };
  }

  async function post(path, body) {
    const startedAt = new Date().toISOString();
    const response = await fetch(path, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    });
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    pushHistory({
      at: startedAt,
      method: "POST",
      path,
      tenant,
      role,
      status: response.status,
      ok: response.ok,
      summary: response.ok ? "ok" : "erro",
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    return payload;
  }

  async function get(path) {
    const startedAt = new Date().toISOString();
    const response = await fetch(path, { headers: authHeaders() });
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    pushHistory({
      at: startedAt,
      method: "GET",
      path,
      tenant,
      role,
      status: response.status,
      ok: response.ok,
      summary: response.ok ? "ok" : "erro",
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    return payload;
  }

  async function createProject() {
    setLoading(true);
    try {
      const payload = await post("/universal/projects", {
        tenant,
        ...projectForm,
        metadata: {
          area: 1200,
          tipologia: "vertical",
          unidades: 140,
          custom_fields: { origem: "command-center" },
        },
      });
      setProject(payload.project);
      setStatus("Projeto universal criado com codigo-mae e metadata dinamica.");
    } catch (_error) {
      setStatus("Falha ao criar projeto. Verifique role/tenant e disponibilidade da API.");
    } finally {
      setLoading(false);
    }
  }

  async function runDecision() {
    setLoading(true);
    try {
      const payload = await post("/universal/decision/score", {
        tenant,
        retorno: 145,
        risco: 35,
        demanda: 95,
        weights: { retorno: 0.5, risco: 0.3, demanda: 0.2 },
      });
      setScore(payload);
      setStatus("Score universal recalculado com pesos configurados.");
    } catch (_error) {
      setStatus("Falha ao calcular score no motor de decisao universal.");
    } finally {
      setLoading(false);
    }
  }

  async function runHealth() {
    setLoading(true);
    try {
      const payload = await post("/universal/health/score", {
        tenant,
        finance: 78,
        operational: 74,
        risk: 66,
      });
      setHealth(payload);
      setStatus("Health Score universal atualizado.");
    } catch (_error) {
      setStatus("Falha ao calcular health score.");
    } finally {
      setLoading(false);
    }
  }

  async function simulateEvents() {
    setLoading(true);
    try {
      await post("/universal/events/simulate", {
        tenant,
        event_types: ["project.created", "project.approved", "project.started", "project.closed"],
        payload: { project_id: project?.id || "SIM-CORE" },
      });
      setStatus("Envelope e simulador de eventos executados no tenant selecionado.");
    } catch (_error) {
      setStatus("Falha ao simular eventos universais.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshDashboard() {
    setLoading(true);
    try {
      const payload = await get(`/universal/dashboard?tenant=${encodeURIComponent(tenant)}`);
      setDashboard(payload);
      setStatus("Dashboard universal atualizado com status, risco e alertas.");
    } catch (_error) {
      setStatus("Falha ao carregar dashboard universal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel universal-cc">
      <div className="universal-cc-head">
        <div>
          <h2 className="panel-title">Universal Command Center</h2>
          <p className="panel-subtitle">Operar o Core Universal com RBAC e isolamento por tenant.</p>
        </div>
      </div>

      <div className="universal-cc-auth">
        <label>
          Tenant
          <select value={tenant} onChange={(event) => setTenant(event.target.value)}>
            {TENANTS.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Role
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            {ROLES.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="universal-cc-grid">
        <article className="stress-kpi">
          <div className="kpi-label">Projeto universal</div>
          <div className="universal-inline-grid">
            <input value={projectForm.portfolio} onChange={(event) => setProjectForm((prev) => ({ ...prev, portfolio: event.target.value }))} />
            <input value={projectForm.program} onChange={(event) => setProjectForm((prev) => ({ ...prev, program: event.target.value }))} />
            <input value={projectForm.project} onChange={(event) => setProjectForm((prev) => ({ ...prev, project: event.target.value }))} />
          </div>
          <button className="btn-primary" disabled={loading} onClick={createProject}>Criar projeto</button>
          <div className="stress-action-meta">{project?.mother_code || "sem codigo-mae"}</div>
        </article>

        <article className="stress-kpi">
          <div className="kpi-label">Decisao e Saude</div>
          <div className="universal-btn-row">
            <button className="btn-secondary pd-secondary" disabled={loading} onClick={runDecision}>Score</button>
            <button className="btn-secondary pd-secondary" disabled={loading} onClick={runHealth}>Health</button>
          </div>
          <div className="stress-action-meta">score: {score?.score ?? "n/a"} | decisao: {score?.decision || "n/a"}</div>
          <div className="stress-action-meta">health: {health?.overall ?? "n/a"} | status: {health?.status || "n/a"}</div>
        </article>

        <article className="stress-kpi">
          <div className="kpi-label">Eventos e Dashboard</div>
          <div className="universal-btn-row">
            <button className="btn-secondary pd-secondary" disabled={loading} onClick={simulateEvents}>Simular eventos</button>
            <button className="btn-secondary pd-secondary" disabled={loading} onClick={refreshDashboard}>Atualizar dashboard</button>
          </div>
          <div className="stress-action-meta">status: {dashboard?.status || "n/a"}</div>
          <div className="stress-action-meta">alertas: {(dashboard?.alerts || []).join(" | ") || "sem alertas"}</div>
        </article>
      </div>

      <div className="signal-item universal-status">{status}</div>

      <div className="stress-kpi universal-history">
        <div className="universal-history-head">
          <div className="kpi-label">Historico de operacoes</div>
          <button
            className="btn-secondary pd-secondary universal-export-btn"
            onClick={exportHistoryJson}
            disabled={history.length === 0}
          >
            Baixar historico JSON
          </button>
        </div>
        <div className="universal-history-list">
          {(history.length ? history : [{ at: "", summary: "Sem operacoes ainda." }]).map((item, index) => (
            <div key={`${item.at}-${item.path || index}`} className="signal-item universal-history-item">
              <strong>{item.method ? `${item.method} ${item.path}` : item.summary}</strong>
              <p>
                {item.at ? `${item.at} | ${item.tenant} | ${item.role} | HTTP ${item.status}` : "Execute uma acao para registrar historico."}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
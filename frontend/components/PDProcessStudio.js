import { useEffect, useMemo, useState } from "react";

const SAMPLE_DSL = `name: Protocolo de Entrega em Chuva
domain: obra
steps:
  - id: vistoria_inicial
    type: checklist
    required: true
  - id: acionar_cobertura
    type: action
    required: true
    depends_on:
      - vistoria_inicial
  - id: registrar_ocorrencia
    type: evidence
    required: true
    depends_on:
      - acionar_cobertura
rules:
  - condition: clima == chuva
    action: priorizar_protocolo_molhado
outputs:
  - playbook_entrega_chuva
`;

const FALLBACK_PROCESS = {
  process: {
    name: "Protocolo de Entrega em Chuva",
    version: 1,
    steps: [
      { id: "vistoria_inicial", type: "checklist" },
      { id: "acionar_cobertura", type: "action" },
      { id: "registrar_ocorrencia", type: "evidence" },
    ],
  },
};

function normalizeProcessShape(payload) {
  const raw = payload || {};
  if (raw.process && raw.process.id) {
    return raw;
  }

  const structured = Array.isArray(raw.structured_steps) ? raw.structured_steps : [];
  const steps = structured.length
    ? structured.map((item) => ({ id: item.id, type: item.type || "step" }))
    : Array.isArray(raw.steps)
      ? raw.steps.map((item) => (typeof item === "string" ? { id: item, type: "step" } : item))
      : FALLBACK_PROCESS.process.steps;

  return {
    process: {
      id: raw.id || "local-process-1",
      name: raw.name || FALLBACK_PROCESS.process.name,
      version: raw.version || 1,
      steps,
    },
  };
}

function extractStepIds(dsl) {
  return dsl
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- id:"))
    .map((line) => line.replace("- id:", "").trim())
    .filter(Boolean);
}

function extractName(dsl) {
  const line = dsl.split("\n").find((item) => item.trim().startsWith("name:"));
  return line ? line.split(":").slice(1).join(":").trim() : FALLBACK_PROCESS.process.name;
}

export default function PDProcessStudio() {
  const [dsl, setDsl] = useState(SAMPLE_DSL);
  const [source, setSource] = useState("local");
  const [status, setStatus] = useState("Pronto para criar, simular e rodar.");
  const [processData, setProcessData] = useState(FALLBACK_PROCESS);
  const [simulation, setSimulation] = useState(null);
  const [execution, setExecution] = useState(null);
  const [audit, setAudit] = useState(null);
  const [john, setJohn] = useState(null);
  const [versions, setVersions] = useState([{ version: "v1", note: "seed inicial" }]);
  const [processOptions, setProcessOptions] = useState([]);
  const [selectedProcessName, setSelectedProcessName] = useState("");
  const [executionHistory, setExecutionHistory] = useState([]);
  const [compareFromVersion, setCompareFromVersion] = useState("");
  const [compareToVersion, setCompareToVersion] = useState("");
  const [compareResult, setCompareResult] = useState(null);
  const [topics, setTopics] = useState([]);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [loading, setLoading] = useState(false);

  const currentProcess = processData?.process || FALLBACK_PROCESS.process;
  const currentProcessId = currentProcess.id;
  const currentProcessName = currentProcess.name;

  async function postGateway(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`gateway status ${response.status}`);
    }

    return response.json();
  }

  async function getGateway(path) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`gateway status ${response.status}`);
    }
    const payload = await response.json();
    return payload.result || payload;
  }

  function applyLocalCreate() {
    const steps = extractStepIds(dsl).map((id) => ({ id, type: "step" }));
    const fallback = {
      process: {
        id: "local-process-1",
        name: extractName(dsl),
        version: 1,
        steps,
      },
    };
    setProcessData(fallback);
    setSource("fallback local");
    setStatus("Gateway indisponivel. DSL materializada localmente para continuar o fluxo.");
    return fallback;
  }

  async function handleCreate() {
    setLoading(true);
    try {
      const payload = await postGateway("/gateway/pd/processes/dsl", {
        name: extractName(dsl),
        domain: "obra",
        dsl,
      });
      const result = payload.result || payload;
      const normalized = normalizeProcessShape(result);
      setProcessData(normalized);
      setSelectedProcessName(normalized?.process?.name || extractName(dsl));
      setVersions((prev) => {
        const nextVersion = String(normalized?.process?.version || "v1");
        const next = prev.filter((item) => item.version !== nextVersion);
        next.push({ version: nextVersion, note: "dsl publicada" });
        return next;
      });
      setSource("gateway pd");
      setStatus("DSL publicada no PD Engine e versionada no gateway.");
      await refreshRuntimeData(normalized?.process?.name || extractName(dsl), true);
    } catch (_error) {
      const fallback = applyLocalCreate();
      setVersions((prev) => {
        const nextVersion = `v${prev.length + 1}`;
        return [...prev, { version: nextVersion, note: "fallback local" }];
      });
      setTopics((prev) => (prev.length ? prev : ["pd.process.updated.v1", "process.step.completed.v1"]));
      setLastRefresh(new Date().toISOString());
      setProcessData(fallback);
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulate() {
    setLoading(true);
    try {
      const payload = await postGateway("/gateway/pd/processes/simulate", {
        process_id: currentProcessId,
        scenario: "chuva",
      });
      setSimulation(payload.result || payload);
      setSource("gateway pd");
      setStatus("Simulacao executada com cenario de chuva.");
    } catch (_error) {
      const steps = processData?.process?.steps || FALLBACK_PROCESS.process.steps;
      setSimulation({
        scenario: "chuva",
        completed_steps: steps.map((step) => step.id),
        bottlenecks: ["registrar evidencias fotograficas antes da liberacao final"],
      });
      setSource("fallback local");
      setStatus("Simulacao local aplicada para inspecionar gargalos mesmo sem gateway.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRun() {
    setLoading(true);
    try {
      const payload = await postGateway("/gateway/pd/processes/run", {
        process_id: currentProcessId,
        actor: "command-center",
        context: { project_id: "obra-norte", clima: "chuva", executor: "command-center" },
      });
      const result = payload.result || payload;
      setExecution(result.execution || result);
      setSource("gateway pd");
      setStatus("Execucao registrada no PD Engine com contexto operacional.");
      await refreshRuntimeData(currentProcessName || extractName(dsl));
    } catch (_error) {
      const steps = processData?.process?.steps || FALLBACK_PROCESS.process.steps;
      setExecution({
        id: "local-exec-1",
        completed_steps: steps.map((step) => step.id),
        pending_steps: [],
      });
      setSource("fallback local");
      setStatus("Execucao local concluida para manter o review operacional no workspace.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAuditAndJohn() {
    const currentExecution = execution || { id: "local-exec-1", completed_steps: extractStepIds(dsl) };

    setLoading(true);
    try {
      const auditPayload = await postGateway("/gateway/pd/processes/audit-validate", {
        execution_id: currentExecution.id,
      });
      const johnPayload = await postGateway("/gateway/pd/processes/john-interpret", {
        execution_id: currentExecution.id,
      });
      setAudit(auditPayload.result || auditPayload);
      setJohn(johnPayload.result || johnPayload);
      setSource("gateway pd");
      setStatus("Auditoria validada e insight do John atualizado.");
      await refreshRuntimeData(currentProcessName || extractName(dsl));
    } catch (_error) {
      const completed = currentExecution.completed_steps || [];
      setAudit({ ok: completed.length > 0, skipped_steps: [], adherence: 1 });
      setJohn({
        insight: {
          summary: completed.length > 2 ? "Fluxo consistente e pronto para nova versao." : "Fluxo ainda curto; coletar mais execucoes.",
          recommended_version_bump: completed.length > 2,
        },
      });
      setSource("fallback local");
      setStatus("Auditoria e leitura do John geradas localmente como contingencia.");
      setTopics((prev) => (prev.length ? prev : ["pd.audit.validated.v1", "pd.john.interpreted.v1"]));
      setLastRefresh(new Date().toISOString());
    } finally {
      setLoading(false);
    }
  }

  async function refreshRuntimeData(processName, resetCompare = false) {
    const [dashboard, eventData] = await Promise.all([
      getGateway("/gateway/pd/dashboard?process_name="),
      getGateway("/gateway/pd/events/published"),
    ]);

    const allProcesses = Array.isArray(dashboard?.processes) ? dashboard.processes : [];
    const uniqueNames = Array.from(new Set(allProcesses.map((item) => item.name).filter(Boolean)));
    setProcessOptions(uniqueNames);

    const requested = processName || selectedProcessName || currentProcessName || extractName(dsl);
    const chosen = uniqueNames.includes(requested) ? requested : (uniqueNames[0] || requested || "");
    if (chosen) {
      setSelectedProcessName(chosen);
    }

    const activeVersions = chosen
      ? allProcesses.filter((item) => item.name === chosen)
      : allProcesses;
    const active = activeVersions[0] || null;

    if (chosen) {
      const versionsData = await getGateway(`/gateway/pd/processes/versions?process_name=${encodeURIComponent(chosen)}&limit=20`);
      const versionRows = Array.isArray(versionsData?.versions) ? versionsData.versions : [];
      setVersions(versionRows.map((item) => ({ version: String(item.version), note: item.created_at || "snapshot" })));

      let fromVersion = compareFromVersion;
      let toVersion = compareToVersion;
      if (resetCompare || !fromVersion || !toVersion) {
        toVersion = versionRows[0]?.version || "";
        fromVersion = versionRows[1]?.version || versionRows[0]?.version || "";
        setCompareFromVersion(fromVersion);
        setCompareToVersion(toVersion);
      }

      if (fromVersion && toVersion) {
        const compare = await getGateway(
          `/gateway/pd/processes/compare?process_name=${encodeURIComponent(chosen)}&from_version=${encodeURIComponent(fromVersion)}&to_version=${encodeURIComponent(toVersion)}`,
        );
        setCompareResult(compare);
      }
    }

    if (active?.id) {
      const history = await getGateway(`/gateway/pd/executions?process_id=${encodeURIComponent(active.id)}&status=&limit=20`);
      setExecutionHistory(Array.isArray(history?.executions) ? history.executions : []);
    } else {
      setExecutionHistory([]);
    }

    setTopics(Array.isArray(eventData?.topics) ? eventData.topics : []);
    setLastRefresh(new Date().toISOString());
  }

  useEffect(() => {
    let active = true;

    async function loadInitialRuntime() {
      try {
        await refreshRuntimeData(processData?.process?.name || extractName(dsl), true);
        if (active) {
          setSource("gateway pd");
        }
      } catch (_error) {
        if (active) {
          setSource("fallback local");
        }
      }
    }

    loadInitialRuntime();
    return () => {
      active = false;
    };
  }, []);

  const orderedVersions = useMemo(() => {
    const rank = (value) => {
      const raw = String(value || "").replace(/^v/i, "");
      const num = Number(raw);
      return Number.isFinite(num) ? num : 0;
    };
    return [...versions].sort((a, b) => rank(b.version) - rank(a.version));
  }, [versions]);

  const steps = currentProcess.steps || FALLBACK_PROCESS.process.steps;

  return (
    <section className="panel pd-studio">
      <div className="pd-studio-head">
        <div>
          <h2 className="panel-title">P&D Studio</h2>
          <p className="panel-subtitle">Editar a Process DSL, simular cenarios, rodar o fluxo e colher insight do John.</p>
        </div>
        <div className="sim-source">Fonte: {source}</div>
      </div>

      <div className="pd-studio-grid">
        <div className="pd-editor-card">
          <div className="table-title">DSL do processo</div>
          <textarea className="pd-dsl-editor" value={dsl} onChange={(event) => setDsl(event.target.value)} />
          <div className="pd-action-row">
            <button className="btn-primary" onClick={handleCreate} disabled={loading}>Versionar DSL</button>
            <button className="btn-secondary pd-secondary" onClick={handleSimulate} disabled={loading}>Simular chuva</button>
            <button className="btn-secondary pd-secondary" onClick={handleRun} disabled={loading}>Rodar fluxo</button>
            <button className="btn-secondary pd-secondary" onClick={handleAuditAndJohn} disabled={loading}>Auditar + John</button>
          </div>
          <div className="signal-item pd-status">{status}</div>
        </div>

        <div className="pd-side-stack">
          <article className="stress-kpi pd-card-accent">
            <div className="kpi-label">Processo ativo</div>
            <div className="stress-action-value">{currentProcessName || FALLBACK_PROCESS.process.name}</div>
            <div className="stress-action-meta">versao {currentProcess.version || 1}</div>
          </article>

          <article className="stress-kpi">
            <div className="kpi-label">Steps mapeados</div>
            <div className="pd-step-list">
              {steps.map((step) => (
                <div key={step.id} className="signal-item">
                  <strong>{step.id}</strong>
                  <p>{step.type || "step"}</p>
                </div>
              ))}
            </div>
          </article>
        </div>
      </div>

      <div className="pd-results-grid">
        <article className="stress-kpi">
          <div className="kpi-label">Simulacao</div>
          <div className="stress-action-value">{simulation?.scenario || "nao executada"}</div>
          <div className="stress-action-meta">steps concluidos: {(simulation?.completed_steps || []).length}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Execucao</div>
          <div className="stress-action-value">{execution?.id || "aguardando"}</div>
          <div className="stress-action-meta">pendentes: {(execution?.pending_steps || []).length}</div>
        </article>
        <article className="stress-kpi">
          <div className="kpi-label">Auditoria</div>
          <div className="stress-action-value">{audit?.ok ? "aderente" : "pendente"}</div>
          <div className="stress-action-meta">aderencia: {Math.round(Number(audit?.adherence || 0) * 100)}%</div>
        </article>
        <article className="stress-kpi pd-card-accent">
          <div className="kpi-label">John</div>
          <div className="stress-action-value">{john?.insight?.recommended_version_bump ? "subir versao" : "monitorar"}</div>
          <div className="stress-action-meta">{john?.insight?.summary || "Sem insight ainda"}</div>
        </article>
      </div>

      <div className="pd-runtime-grid">
        <article className="stress-kpi">
          <div className="kpi-label">Filtro e comparacao</div>
          <label className="pd-inline-label">
            Processo
            <select
              className="pd-select"
              value={selectedProcessName}
              onChange={(event) => {
                const name = event.target.value;
                setSelectedProcessName(name);
                refreshRuntimeData(name, true).catch(() => {
                  setStatus("Nao foi possivel atualizar comparacao neste momento.");
                });
              }}
            >
              {(processOptions.length ? processOptions : [currentProcessName]).map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <div className="pd-inline-grid">
            <label className="pd-inline-label">
              De
              <select className="pd-select" value={compareFromVersion} onChange={(event) => setCompareFromVersion(event.target.value)}>
                {orderedVersions.map((item) => (
                  <option key={`from-${item.version}`} value={item.version}>{item.version}</option>
                ))}
              </select>
            </label>
            <label className="pd-inline-label">
              Para
              <select className="pd-select" value={compareToVersion} onChange={(event) => setCompareToVersion(event.target.value)}>
                {orderedVersions.map((item) => (
                  <option key={`to-${item.version}`} value={item.version}>{item.version}</option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="btn-secondary pd-secondary"
            onClick={async () => {
              if (!selectedProcessName || !compareFromVersion || !compareToVersion) {
                return;
              }
              try {
                const compare = await getGateway(
                  `/gateway/pd/processes/compare?process_name=${encodeURIComponent(selectedProcessName)}&from_version=${encodeURIComponent(compareFromVersion)}&to_version=${encodeURIComponent(compareToVersion)}`,
                );
                setCompareResult(compare);
                setStatus("Comparacao de versoes atualizada.");
              } catch (_error) {
                setStatus("Falha ao comparar versoes no gateway.");
              }
            }}
            disabled={loading}
          >
            Comparar versoes
          </button>
          <div className="pd-compare-box">
            <div className="pd-compare-col">
              <strong>Adicionados</strong>
              {(compareResult?.diff?.added || []).map((item) => <div key={`add-${item}`} className="signal-item">{item}</div>)}
            </div>
            <div className="pd-compare-col">
              <strong>Removidos</strong>
              {(compareResult?.diff?.removed || []).map((item) => <div key={`rem-${item}`} className="signal-item">{item}</div>)}
            </div>
          </div>
        </article>

        <article className="stress-kpi">
          <div className="kpi-label">Historico de versoes</div>
          <div className="pd-runtime-list">
            {orderedVersions.map((item) => (
              <div key={`${item.version}-${item.note}`} className="signal-item">
                <strong>v{item.version}</strong>
                <p>{item.note}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="stress-kpi">
          <div className="kpi-label">Eventos publicados</div>
          <div className="pd-runtime-list">
            {(topics.length ? topics : ["sem eventos"]).map((topic) => (
              <div key={topic} className="signal-item pd-topic-item">{topic}</div>
            ))}
          </div>
          <div className="stress-action-meta">ultima leitura: {lastRefresh || "n/a"}</div>
        </article>

        <article className="stress-kpi">
          <div className="kpi-label">Historico de execucoes</div>
          <div className="pd-runtime-list">
            {(executionHistory.length ? executionHistory : [{ id: "n/a", status: "sem execucoes" }]).map((item) => (
              <div key={item.id} className="signal-item">
                <strong>{item.status}</strong>
                <p>{item.version || "v?"} | {item.current_step || "n/a"}</p>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
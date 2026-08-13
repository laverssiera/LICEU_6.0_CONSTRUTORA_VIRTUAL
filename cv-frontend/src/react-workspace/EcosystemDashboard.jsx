import { useCallback, useEffect, useRef, useState } from 'react';
import DecisionLayer from './DecisionLayer.jsx';
import AutonomousControl from './AutonomousControl.jsx';
import InnovationPanel from './InnovationPanel.jsx';
import ExecutiveControl from './ExecutiveControl.jsx';
import ChangeApprovalPanel from './ChangeApprovalPanel.jsx';
import ChangeHeatmapPanel from './ChangeHeatmapPanel.jsx';
import ExecutiveCockpitPanel from './ExecutiveCockpitPanel.jsx';
import { resolvedApiBaseUrl, resolvedWsBaseUrl } from '@/services/runtimeConfig';
import { useCurrentUser } from './useCurrentUser';

const API = resolvedApiBaseUrl;
const WS_BASE = resolvedWsBaseUrl;

const STAGE_LABELS = {
  leads: 'Leads',
  negotiation: 'Negociação',
  proposal: 'Proposta',
  juridico: 'Jurídico',
  closed: 'Fechado',
};

const MONOLITH_LABELS = {
  archimedes: 'Archimedes',
  juridicotech: 'JuridicoTech',
  hubbackoffice: 'HubBackoffice',
  cefeida: 'CEFEIDA',
  gamemkt: 'GameMKT',
  john: 'John AI',
  academia: 'Academia',
  cea_invest: 'CEA Invest',
  econo_tech: 'EconoTech',
};

function money(v) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(Number(v || 0));
}

function statusColor(status) {
  if (status === 'up' || status === 'active') return '#22c55e';
  if (status === 'degraded') return '#f59e0b';
  return '#64748b';
}

function riskColor(risk) {
  if (risk === 'high') return '#ef4444';
  if (risk === 'medium') return '#f59e0b';
  if (risk === 'low') return '#22c55e';
  return '#94a3b8';
}

// ─── small primitives ────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: 'linear-gradient(135deg,#0f172a 60%,#1e293b)',
      border: `1px solid ${accent || '#334155'}`,
      borderRadius: 16,
      padding: '1rem 1.25rem',
      display: 'flex', flexDirection: 'column', gap: 2,
    }}>
      <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#94a3b8' }}>{label}</span>
      <strong style={{ fontSize: 24, color: accent || '#f1f5f9', lineHeight: 1 }}>{value}</strong>
      {sub !== undefined && <span style={{ fontSize: 12, color: '#64748b' }}>{sub}</span>}
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <h2 style={{
      fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.14em',
      color: '#94a3b8', margin: '0 0 0.6rem', paddingBottom: '0.4rem',
      borderBottom: '1px solid #1e293b',
    }}>{children}</h2>
  );
}

// ─── panel components ─────────────────────────────────────────────────────────

function KpisPanel({ kpis, financeiro }) {
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>KPIs Globais</SectionTitle>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
        <KpiCard label="Receita" value={money(kpis.estimated_revenue)} accent="#22c55e" />
        <KpiCard label="Pipeline" value={money(kpis.pipeline_value)} accent="#3b82f6" />
        <KpiCard label="Leads ativos" value={kpis.active_leads} accent="#a855f7" />
        <KpiCard label="Deals ativos" value={kpis.active_deals} accent="#f59e0b" />
        <KpiCard label="Conversão" value={`${kpis.conversion_rate}%`} accent="#06b6d4" />
        <KpiCard label="Alto risco" value={kpis.high_risk_cards} accent="#ef4444" />
      </div>
      {/* Painel de aprovação de mudanças */}
      <ChangeApprovalPanel />
    </div>
  );
}

function FinanceiroPanel({ financeiro }) {
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Financeiro (HubBackoffice)</SectionTitle>
      <KpiCard label="Receita fechada" value={money(financeiro.estimated_revenue)} accent="#22c55e" />
      <KpiCard label="Pipeline total" value={money(financeiro.pipeline_value)} accent="#38bdf8" />
      <KpiCard
        label="Contas a receber"
        value={money(financeiro.accounts_receivable)}
        sub="proposta + jurídico"
        accent="#a3e635"
      />
      <KpiCard
        label="Contas a pagar"
        value={money(financeiro.accounts_payable)}
        sub="leads + negociação"
        accent="#fb923c"
      />
    </div>
  );
}

function PerformancePanel({ performance }) {
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Performance (John Layer)</SectionTitle>
      <div style={{ display: 'grid', gap: '0.4rem', maxHeight: 320, overflowY: 'auto' }}>
        {performance.map((p) => (
          <div key={p.source} style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderRadius: 10, padding: '0.6rem 0.8rem',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 12, color: '#cbd5e1' }}>
              {MONOLITH_LABELS[p.source] || p.source}
            </span>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 12, color: '#22c55e' }}>{money(p.revenue)}</div>
              <div style={{ fontSize: 10, color: '#64748b' }}>{p.closed}/{p.cards} fechados</div>
            </div>
          </div>
        ))}
        {performance.length === 0 && (
          <p style={{ fontSize: 12, color: '#64748b' }}>Sem dados de performance ainda.</p>
        )}
      </div>
    </div>
  );
}

function PipelinePanel({ funnel }) {
  const max = Math.max(...funnel.map((f) => f.count || 0), 1);
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Pipeline Global</SectionTitle>
      <div style={{ display: 'grid', gap: '0.5rem' }}>
        {funnel.map((f) => (
          <div key={f.stage} style={{ display: 'grid', gap: 4 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#cbd5e1' }}>
              <span>{STAGE_LABELS[f.stage] || f.stage}</span>
              <span style={{ color: '#94a3b8' }}>{f.count} · {money(f.value)}</span>
            </div>
            <div style={{ height: 6, background: '#1e293b', borderRadius: 99 }}>
              <div style={{
                height: 6, borderRadius: 99,
                width: `${(f.count / max) * 100}%`,
                background: f.stage === 'closed' ? '#22c55e'
                  : f.stage === 'juridico' ? '#a855f7'
                  : f.stage === 'proposal' ? '#3b82f6'
                  : f.stage === 'negotiation' ? '#f59e0b'
                  : '#64748b',
                transition: 'width 0.4s ease',
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MonolithPanel({ monoliths }) {
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Status dos Monólitos</SectionTitle>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
        {monoliths.map((m) => (
          <div key={m.name} style={{
            background: '#0f172a', border: '1px solid #1e293b',
            borderRadius: 10, padding: '0.6rem 0.8rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: statusColor(m.status), display: 'inline-block', flexShrink: 0,
              }} />
              <span style={{ fontSize: 11, color: '#e2e8f0' }}>
                {MONOLITH_LABELS[m.name] || m.name}
              </span>
            </div>
            <div style={{ marginTop: 4, fontSize: 10, color: '#64748b' }}>
              {m.event_volume} eventos · {m.card_volume} cards
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskPanel({ risks }) {
  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Risco Crítico</SectionTitle>
      {risks.length === 0 && (
        <p style={{ fontSize: 12, color: '#22c55e' }}>Nenhum risco detectado.</p>
      )}
      <div style={{ display: 'grid', gap: '0.4rem', maxHeight: 260, overflowY: 'auto' }}>
        {risks.map((r) => (
          <div key={r.card_id} style={{
            background: '#0f172a',
            borderLeft: `3px solid ${riskColor(r.risk)}`,
            borderRadius: '0 10px 10px 0', padding: '0.5rem 0.75rem',
          }}>
            <div style={{ fontSize: 12, color: '#f1f5f9', fontWeight: 600 }}>{r.title}</div>
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>
              {r.stage} · {money(r.value)}
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
              {r.alerts.map((a) => (
                <span key={a} style={{
                  fontSize: 9, background: '#1e293b', color: '#f87171',
                  borderRadius: 4, padding: '2px 6px',
                }}>{a}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventStreamPanel({ events }) {
  const EVENT_COLORS = {
    'lead.created': '#a855f7',
    'deal.created': '#3b82f6',
    'deal.closed': '#22c55e',
    'proposal.sent': '#f59e0b',
    'contract.created': '#06b6d4',
    'contract.signed': '#22d3ee',
    'payment.generated': '#4ade80',
    'bypass.detected': '#ef4444',
    'john.suggestion': '#facc15',
  };

  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <SectionTitle>Event Stream (Realtime — /events/ws)</SectionTitle>
      <div style={{
        display: 'grid', gap: '0.3rem',
        maxHeight: 200, overflowY: 'auto',
        padding: '0.5rem',
        background: '#020617',
        borderRadius: 12,
        fontFamily: 'monospace',
      }}>
        {events.length === 0 && (
          <span style={{ fontSize: 11, color: '#475569' }}>Aguardando eventos…</span>
        )}
        {events.map((e, i) => {
          const type = e.event_type || e.type || (e.event || {}).event_type || 'event';
          const src = e.source || (e.event || {}).source || '';
          const ts = e.occurred_at || e.timestamp || new Date().toISOString();
          const color = EVENT_COLORS[type] || '#64748b';
          return (
            <div key={i} style={{ fontSize: 11, display: 'flex', gap: 8 }}>
              <span style={{ color: '#334155', flexShrink: 0 }}>
                {ts.slice(11, 19)}
              </span>
              <span style={{ color, fontWeight: 600 }}>{type}</span>
              {src && <span style={{ color: '#475569' }}>· {src}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── main ─────────────────────────────────────────────────────────────────────

export default function EcosystemDashboard() {
  const [data, setData] = useState(null);
  const [wsEvents, setWsEvents] = useState([]);
  const [warMode, setWarMode] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const user = useCurrentUser();
  const wsRef = useRef(null);

  const loadMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${API}/metrics`);
      const json = await res.json();
      setData(json.data);
      setLastUpdated(new Date().toLocaleTimeString('pt-BR'));
      const risks = json.data?.risk_signals || [];
      setWarMode(risks.some((r) => r.risk === 'high'));
    } catch (_) {
      // Server offline — keep last snapshot
    }
  }, []);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 15000);
    return () => clearInterval(interval);
  }, [loadMetrics]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/events/ws`);
    wsRef.current = ws;

    ws.onmessage = (msg) => {
      try {
        const envelope = JSON.parse(msg.data);
        const ev = envelope?.event || envelope;
        setWsEvents((prev) => [ev, ...prev.slice(0, 49)]);
      } catch (_) {}
    };

    return () => ws.close();
  }, []);

  if (!data) {
    return (
      <div style={{ background: '#020617', color: '#64748b', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'monospace' }}>
        Carregando Telaão LICEU 6.0…
      </div>
    );
  }

  const allEvents = [...wsEvents, ...(data.recent_events || [])].slice(0, 50);

  return (
    <div style={{
      background: warMode ? '#0c0404' : '#020617',
      color: '#f1f5f9',
      minHeight: '100vh',
      fontFamily: "'Inter', sans-serif",
      padding: '1rem',
      transition: 'background 0.5s',
    }}>
      {/* HEADER */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        background: '#0f172a',
        border: `1px solid ${warMode ? '#ef4444' : '#1e293b'}`,
        borderRadius: 14, marginBottom: '1rem',
      }}>
        <div>
          <span style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#64748b' }}>LICEU 6.0</span>
          <h1 style={{ margin: 0, fontSize: 18, color: warMode ? '#ef4444' : '#facc15' }}>
            ECOSYSTEM CONTROL {warMode && '🔴 MODO GUERRA'}
          </h1>
        </div>
        <div style={{ textAlign: 'right', fontSize: 11, color: '#475569' }}>
          <div>{data.kpis?.total_cards} cards ativos</div>
          <div>{lastUpdated && `Atualizado ${lastUpdated}`}</div>
        </div>
      </header>

      {/* MAIN GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gridTemplateRows: 'auto auto auto auto',
        gap: '1rem',
      }}>
        {/* Row 1 */}
        <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <KpisPanel kpis={data.kpis || {}} financeiro={data.financeiro || {}} />
        </div>
        <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <FinanceiroPanel financeiro={data.financeiro || {}} />
        </div>
        <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <PerformancePanel performance={data.performance || []} />
        </div>

        {/* Row 2 */}
        <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <PipelinePanel funnel={data.funnel || []} />
        </div>
        <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <MonolithPanel monoliths={data.monolith_status || []} />
        </div>
        <div style={{ background: '#0b1120', border: `1px solid ${warMode ? '#ef4444' : '#1e293b'}`, borderRadius: 18, padding: '1.2rem' }}>
          <RiskPanel risks={data.risk_signals || []} />
        </div>

        {/* Row 3: Event Stream full width */}
        <div style={{ gridColumn: '1 / -1', background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <EventStreamPanel events={allEvents} />
        </div>

        {/* Row 4: Control engines */}
        <div style={{
          background: '#0b1120',
          border: `1px solid ${warMode ? '#ef444444' : '#1e3a5f'}`,
          borderRadius: 18, padding: '1.2rem',
        }}>
          <InnovationPanel />
        </div>
        <div style={{
          background: '#0b1120',
          border: `1px solid ${warMode ? '#ef444444' : '#1e3a5f'}`,
          borderRadius: 18, padding: '1.2rem',
        }}>
          <AutonomousControl />
        </div>
        <div style={{
          background: '#0b1120',
          border: `1px solid ${warMode ? '#ef444444' : '#1e3a5f'}`,
          borderRadius: 18, padding: '1.2rem',
        }}>
          <DecisionLayer />
        </div>

        {/* Row 5: Executive control full width */}
        <div style={{ gridColumn: '1 / -1', background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem' }}>
          <ExecutiveControl />
        </div>

        {/* Painel de aprovação de mudanças global */}
        <div style={{ gridColumn: '1 / -1' }}>
          <ChangeApprovalPanel user={user} />
        </div>

        {/* Painel de Change Heatmap global */}
        <div style={{ gridColumn: '1 / -1' }}>
          <ChangeHeatmapPanel />
        </div>

        {/* Painel executivo CEO Cockpit */}
        <div style={{ gridColumn: '1 / -1' }}>
          <ExecutiveCockpitPanel />
        </div>
      </div>
    </div>
  );
}

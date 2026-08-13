/**
 * DecisionLayer.jsx — LICEU 6.0 Nível 2
 * Decision Engine em tempo real: lê eventos WS, processa regras, exibe decisões
 * e permite execução de ações diretamente no painel.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { resolvedApiBaseUrl, resolvedWsBaseUrl } from '@/services/runtimeConfig';

const API = resolvedApiBaseUrl;
const WS_BASE = resolvedWsBaseUrl;

// ─── Prioridade → cor ────────────────────────────────────────────────────────
const PRIORITY_COLOR = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#f59e0b',
  LOW:      '#22c55e',
};

const TYPE_ICON = {
  PRIORITY: '🎯',
  ACTION:   '⚡',
  UNLOCK:   '🔓',
  BLOCK:    '🚫',
  FOLLOWUP: '📲',
  INSIGHT:  '💡',
};

// ─── Regras client-side (espelham o backend) ──────────────────────────────── 
function processDecision(event) {
  const et = (event.event_type || '').toLowerCase();
  const src = (event.source || 'unknown');
  const payload = event.payload || {};

  if (et === 'deal_created') return {
    id: crypto.randomUUID(),
    type: 'PRIORITY', priority: 'HIGH',
    message: `Novo deal criado — iniciar qualificação e atribuir corretor`,
    action: 'assign_broker',
    payload: { card_id: payload.card_id || event.card_id, source: src },
    source_event: et, executed: false,
  };

  if (et === 'client_silent' || et === 'lead_inactive') return {
    id: crypto.randomUUID(),
    type: 'FOLLOWUP', priority: 'HIGH',
    message: `Cliente inativo — enviar follow-up automático`,
    action: 'send_whatsapp',
    payload: { phone: payload.phone || '', message: 'Gostaríamos de retomar o contato!' },
    source_event: et, executed: false,
  };

  if (et === 'nda_signed' || et === 'contract_signed') return {
    id: crypto.randomUUID(),
    type: 'UNLOCK', priority: 'HIGH',
    message: `Contrato assinado — liberar imóveis e commissions`,
    action: 'unlock_properties',
    payload: { card_id: payload.card_id || event.card_id },
    source_event: et, executed: false,
  };

  if (et === 'legal_issue_raised' || et === 'compliance_violation') return {
    id: crypto.randomUUID(),
    type: 'BLOCK', priority: 'CRITICAL',
    message: `Pendência jurídica detectada — bloquear avanço do deal`,
    action: 'block_deal',
    payload: { card_id: payload.card_id || event.card_id },
    source_event: et, executed: false,
  };

  if (et === 'commission_released' || et === 'deal_closed') return {
    id: crypto.randomUUID(),
    type: 'INSIGHT', priority: 'MEDIUM',
    message: `Comissão liberada — notificar corretor e financeiro`,
    action: 'notify_commission',
    payload: { card_id: payload.card_id || event.card_id, value: payload.value || 0 },
    source_event: et, executed: false,
  };

  if ((et === 'heartbeat' || et === 'health_check') &&
      (payload.status === 'degraded' || payload.status === 'down')) return {
    id: crypto.randomUUID(),
    type: 'BLOCK', priority: 'CRITICAL',
    message: `Monólito '${src}' em estado '${payload.status}' — triagem de incidente`,
    action: 'trigger_incident',
    payload: { monolith: src, status: payload.status },
    source_event: et, executed: false,
  };

  return null;
}

// ─── Componentes primitivos ───────────────────────────────────────────────── 

function Badge({ text, color }) {
  return (
    <span style={{
      background: color + '22', color, border: `1px solid ${color}44`,
      borderRadius: 6, padding: '2px 8px', fontSize: 10,
      fontWeight: 700, fontFamily: 'monospace', letterSpacing: '0.06em',
    }}>{text}</span>
  );
}

function ActionButton({ label, onClick, executing, done, color = '#3b82f6' }) {
  return (
    <button
      onClick={onClick}
      disabled={executing || done}
      style={{
        background: done ? '#22c55e22' : executing ? '#1e293b' : color + '22',
        color: done ? '#22c55e' : executing ? '#94a3b8' : color,
        border: `1px solid ${done ? '#22c55e44' : color + '44'}`,
        borderRadius: 6, padding: '4px 12px', fontSize: 11, cursor: done ? 'default' : 'pointer',
        fontWeight: 600, transition: 'all 0.2s',
      }}
    >
      {done ? '✓ Executado' : executing ? '⏳ Executando…' : `▶ ${label}`}
    </button>
  );
}

function DecisionCard({ dec, onExecute }) {
  const [executing, setExecuting] = useState(false);
  const [done, setDone]           = useState(dec.executed || false);
  const [result, setResult]       = useState(dec.result || null);

  const pcolor = PRIORITY_COLOR[dec.priority] || '#94a3b8';

  async function handleExecute() {
    if (done) return;
    setExecuting(true);
    try {
      const res = await fetch(`${API}/decisions/${dec.id}/execute`, { method: 'POST' });
      const data = await res.json();
      setResult(data.result);
      setDone(true);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setExecuting(false);
    }
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg,#0f172a 60%,#1e293b)',
      border: `1px solid ${pcolor}44`,
      borderLeft: `3px solid ${pcolor}`,
      borderRadius: 10, padding: '0.75rem 1rem',
      display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      {/* header */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 14 }}>{TYPE_ICON[dec.type] || '•'}</span>
        <Badge text={dec.type}     color={pcolor} />
        <Badge text={dec.priority} color={pcolor} />
        <span style={{ marginLeft: 'auto', fontSize: 10, color: '#475569', fontFamily: 'monospace' }}>
          {dec.source_event}
        </span>
      </div>

      {/* message */}
      <p style={{ margin: 0, fontSize: 13, color: '#cbd5e1', lineHeight: 1.5 }}>{dec.message}</p>

      {/* action + result */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace' }}>
          action: <strong style={{ color: '#93c5fd' }}>{dec.action}</strong>
        </span>
        <ActionButton
          label={dec.action.replace(/_/g, ' ')}
          onClick={handleExecute}
          executing={executing}
          done={done}
          color={pcolor}
        />
      </div>

      {result && (
        <pre style={{
          margin: 0, fontSize: 10, color: '#94a3b8',
          background: '#020617', borderRadius: 6, padding: '6px 8px', overflowX: 'auto',
        }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

// ─── Stats bar ────────────────────────────────────────────────────────────── 

function StatsBar({ decisions }) {
  const counts = decisions.reduce((acc, d) => {
    acc[d.priority] = (acc[d.priority] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: '0.5rem' }}>
      {Object.entries(PRIORITY_COLOR).map(([p, c]) => (
        counts[p] ? (
          <span key={p} style={{
            background: c + '22', color: c, border: `1px solid ${c}44`,
            borderRadius: 6, padding: '2px 10px', fontSize: 11, fontWeight: 700,
          }}>
            {counts[p]} {p}
          </span>
        ) : null
      ))}
      <span style={{ marginLeft: 'auto', fontSize: 11, color: '#475569' }}>
        {decisions.filter(d => d.executed).length} / {decisions.length} executadas
      </span>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────── 

export default function DecisionLayer({ standalone = false }) {
  const [decisions, setDecisions] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [filter, setFilter]           = useState('ALL');
  const wsRef = useRef(null);

  // Carregar decisões persistentes do backend na montagem
  useEffect(() => {
    fetch(`${API}/decisions?limit=30`)
      .then(r => r.json())
      .then(data => {
        if (data.decisions?.length) {
          setDecisions(data.decisions);
        }
      })
      .catch(() => {});
  }, []);

  // WebSocket live decisions
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`${WS_BASE}/events/ws`);
      wsRef.current = ws;

      ws.onopen  = () => setWsConnected(true);
      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000); // auto-reconnect
      };

      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data);

          // Decisão já gerada pelo backend via decision.engine channel
          if (event.event_type === 'decision_generated' && event.payload?.id) {
            setDecisions(prev => {
              if (prev.find(d => d.id === event.payload.id)) return prev;
              return [event.payload, ...prev.slice(0, 49)];
            });
            return;
          }

          // Client-side rules (modo offline / bypass)
          const dec = processDecision(event);
          if (dec) {
            setDecisions(prev => {
              if (prev.find(d => d.source_event === dec.source_event && !d.executed)) return prev;
              return [dec, ...prev.slice(0, 49)];
            });
          }
        } catch (_) {}
      };
    }

    connect();
    return () => wsRef.current?.close();
  }, []);

  const handleExecuteAll = useCallback(async () => {
    const pending = decisions.filter(d => !d.executed && d.priority === 'CRITICAL');
    for (const dec of pending) {
      if (!dec.id) continue;
      try {
        await fetch(`${API}/decisions/${dec.id}/execute`, { method: 'POST' });
      } catch (_) {}
    }
    // Reload decisions
    const freshData = await fetch(`${API}/decisions?limit=30`).then(r => r.json()).catch(() => ({ decisions: [] }));
    if (freshData.decisions?.length) setDecisions(freshData.decisions);
  }, [decisions]);

  const filtered = filter === 'ALL'
    ? decisions
    : decisions.filter(d => d.priority === filter || d.type === filter);

  // ── UI ────────────────────────────────────────────────────────────────────
  const containerStyle = standalone
    ? {
        maxWidth: 900, margin: '0 auto',
        background: '#020617', minHeight: '100vh',
        padding: '1.5rem', fontFamily: 'Inter, system-ui, sans-serif', color: '#f1f5f9',
      }
    : { fontFamily: 'Inter, system-ui, sans-serif', color: '#f1f5f9' };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#94a3b8' }}>
          🧠 Decision Engine
        </h2>
        <span style={{
          width: 8, height: 8, borderRadius: '50%',
          background: wsConnected ? '#22c55e' : '#ef4444',
          boxShadow: wsConnected ? '0 0 6px #22c55e' : 'none',
          display: 'inline-block',
        }} />
        <span style={{ fontSize: 10, color: '#64748b' }}>{wsConnected ? 'LIVE' : 'OFFLINE'}</span>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', flexWrap: 'wrap' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'BLOCK', 'ACTION', 'FOLLOWUP'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                background: filter === f ? '#1e40af' : '#0f172a',
                color: filter === f ? '#bfdbfe' : '#64748b',
                border: `1px solid ${filter === f ? '#3b82f6' : '#1e293b'}`,
                borderRadius: 6, padding: '3px 10px', fontSize: 10, cursor: 'pointer', fontWeight: 600,
              }}
            >{f}</button>
          ))}
        </div>

        {/* Execute all critical */}
        <button
          onClick={handleExecuteAll}
          style={{
            background: '#7f1d1d22', color: '#fca5a5',
            border: '1px solid #7f1d1d', borderRadius: 6,
            padding: '4px 14px', fontSize: 11, cursor: 'pointer', fontWeight: 700,
          }}
        >
          ⚡ Executar todos CRITICAL
        </button>
      </div>

      {/* Stats bar */}
      {decisions.length > 0 && <StatsBar decisions={decisions} />}

      {/* Decision list */}
      {filtered.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '2rem',
          color: '#334155', fontSize: 13,
          border: '1px dashed #1e293b', borderRadius: 12,
        }}>
          Aguardando eventos para gerar decisões…
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {filtered.map((dec, i) => (
            <DecisionCard
              key={dec.id || i}
              dec={dec}
              onExecute={() => {}}
            />
          ))}
        </div>
      )}
    </div>
  );
}

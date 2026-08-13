import { useCallback, useEffect, useState } from 'react';
import { resolvedApiBaseUrl } from '@/services/runtimeConfig';

const API = resolvedApiBaseUrl;
const MODES = ['AUTO', 'SUPERVISED', 'RESTRICTED'];

function badgeStyle(color) {
  return {
    fontSize: 10,
    padding: '3px 8px',
    borderRadius: 999,
    background: `${color}22`,
    border: `1px solid ${color}66`,
    color,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  };
}

function money(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export default function InnovationPanel() {
  const [mode, setMode] = useState('SUPERVISED');
  const [state, setState] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [busy, setBusy] = useState(false);

  const loadInnovation = useCallback(async () => {
    try {
      const response = await fetch(`${API}/innovation/state`);
      const data = await response.json();
      setMode(data.state?.mode || 'SUPERVISED');
      setState(data.state || null);
      setIdeas(data.ideas || []);
    } catch (_) {
      // keep previous state on transient network failures
    }
  }, []);

  useEffect(() => {
    loadInnovation();
    const timer = setInterval(loadInnovation, 20000);
    return () => clearInterval(timer);
  }, [loadInnovation]);

  async function changeMode(nextMode) {
    setBusy(true);
    try {
      await fetch(`${API}/innovation/mode`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: nextMode }),
      });
      await loadInnovation();
    } finally {
      setBusy(false);
    }
  }

  async function evaluateInnovation() {
    setBusy(true);
    try {
      const response = await fetch(`${API}/innovation/evaluate`, { method: 'POST' });
      const data = await response.json();
      setState(data.state || null);
      setIdeas(data.ideas || []);
      setMode(data.mode || mode);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: 'grid', gap: '0.9rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#94a3b8' }}>
          Innovation Engine
        </h2>
        <p style={{ margin: '0.5rem 0 0', fontSize: 12, color: '#64748b' }}>
          Novas fontes de receita sob Budget Guard, Compliance e alinhamento estratégico.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {MODES.map((item) => (
          <button
            key={item}
            type="button"
            disabled={busy}
            onClick={() => changeMode(item)}
            style={{
              padding: '0.55rem 0.85rem',
              borderRadius: 10,
              border: `1px solid ${mode === item ? '#38bdf8' : '#334155'}`,
              background: mode === item ? '#1e293b' : '#020617',
              color: mode === item ? '#38bdf8' : '#cbd5e1',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            {item}
          </button>
        ))}
        <button
          type="button"
          disabled={busy}
          onClick={evaluateInnovation}
          style={{
            padding: '0.55rem 0.85rem',
            borderRadius: 10,
            border: '1px solid #22c55e66',
            background: '#22c55e18',
            color: '#22c55e',
            cursor: 'pointer',
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          Rodar ciclo de inovação
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Budget livre</div>
          <strong style={{ color: '#22c55e', fontSize: 18 }}>{money(state?.available_budget || 0)}</strong>
        </div>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Budget guard</div>
          <strong style={{ color: '#f59e0b', fontSize: 18 }}>{money(state?.budget_guard_limit || 0)}</strong>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 8, maxHeight: 360, overflowY: 'auto' }}>
        {ideas.map((idea) => {
          const blocked = idea.status === 'blocked';
          const statusColor = blocked ? '#ef4444' : idea.status === 'executed' ? '#22c55e' : '#38bdf8';
          return (
            <div
              key={idea.id}
              style={{
                display: 'grid',
                gap: 8,
                padding: '0.8rem 0.9rem',
                borderRadius: 12,
                background: '#0f172a',
                border: `1px solid ${statusColor}33`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                <strong style={{ fontSize: 12, color: '#e2e8f0' }}>{idea.name}</strong>
                <span style={badgeStyle(statusColor)}>{idea.status}</span>
              </div>

              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <span style={badgeStyle('#38bdf8')}>{idea.category}</span>
                <span style={badgeStyle('#a855f7')}>confiança {Math.round((idea.confidence || 0) * 100)}%</span>
                <span style={badgeStyle('#22c55e')}>ROI {idea.expected_roi}x</span>
              </div>

              <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>{idea.rationale}</p>

              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center', fontSize: 11 }}>
                <span style={{ color: '#64748b' }}>{idea.target}</span>
                <span style={{ color: '#f1f5f9' }}>{money(idea.estimated_budget)}</span>
              </div>

              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <span style={badgeStyle(idea.governance?.budget_allowed ? '#22c55e' : '#ef4444')}>budget</span>
                <span style={badgeStyle(idea.governance?.compliance_allowed ? '#22c55e' : '#ef4444')}>compliance</span>
                <span style={badgeStyle(idea.governance?.alignment_allowed ? '#22c55e' : '#ef4444')}>alignment</span>
                <span style={badgeStyle(idea.governance?.risk_allowed ? '#22c55e' : '#ef4444')}>risk</span>
              </div>

              {!!idea.governance?.blocked_reasons?.length && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {idea.governance.blocked_reasons.map((reason) => (
                    <span key={reason} style={badgeStyle('#ef4444')}>{reason}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {ideas.length === 0 && <span style={{ fontSize: 12, color: '#64748b' }}>Nenhuma hipótese de inovação disponível.</span>}
      </div>
    </div>
  );
}
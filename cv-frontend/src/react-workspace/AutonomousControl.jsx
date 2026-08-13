import { useCallback, useEffect, useState } from 'react';
import { resolvedApiBaseUrl } from '@/services/runtimeConfig';

const API = resolvedApiBaseUrl;
const MODES = ['AUTO', 'SEMI', 'MANUAL'];

function SmallBadge({ children, color = '#64748b' }) {
  return (
    <span style={{
      fontSize: 10,
      padding: '3px 8px',
      borderRadius: 999,
      background: `${color}22`,
      border: `1px solid ${color}66`,
      color,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
    }}>
      {children}
    </span>
  );
}

function ActionRow({ item, onRollback }) {
  const color = item.status === 'executed'
    ? '#22c55e'
    : item.status === 'approval_required'
      ? '#f59e0b'
      : item.status === 'rolled_back'
        ? '#94a3b8'
        : '#38bdf8';

  return (
    <div style={{
      display: 'grid', gap: 6,
      padding: '0.7rem 0.8rem',
      borderRadius: 10,
      background: '#0f172a',
      border: `1px solid ${color}44`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
        <strong style={{ fontSize: 12, color: '#e2e8f0' }}>{item.action}</strong>
        <SmallBadge color={color}>{item.status}</SmallBadge>
      </div>
      <span style={{ fontSize: 11, color: '#94a3b8' }}>{item.reason || item.payload?.reason || 'sem motivo informado'}</span>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
        <span style={{ fontSize: 10, color: '#64748b' }}>{item.target || item.payload?.target || 'ecosystem'}</span>
        {item.status !== 'rolled_back' && (
          <button
            type="button"
            onClick={() => onRollback(item.id)}
            style={{
              fontSize: 10,
              padding: '4px 8px',
              borderRadius: 8,
              border: '1px solid #334155',
              background: '#020617',
              color: '#cbd5e1',
              cursor: 'pointer',
            }}
          >
            rollback
          </button>
        )}
      </div>
    </div>
  );
}

export default function AutonomousControl() {
  const [mode, setMode] = useState('SEMI');
  const [stateSnapshot, setStateSnapshot] = useState(null);
  const [actions, setActions] = useState([]);
  const [busy, setBusy] = useState(false);

  const loadState = useCallback(async () => {
    try {
      const response = await fetch(`${API}/autonomous/state`);
      const data = await response.json();
      setMode(data.state?.mode || 'SEMI');
      setStateSnapshot(data.state || null);
      setActions(data.recent_actions || []);
    } catch (_) {
      // keep previous snapshot when API is offline
    }
  }, []);

  useEffect(() => {
    loadState();
    const timer = setInterval(loadState, 15000);
    return () => clearInterval(timer);
  }, [loadState]);

  async function changeMode(nextMode) {
    setBusy(true);
    try {
      await fetch(`${API}/autonomous/mode`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: nextMode }),
      });
      await loadState();
    } finally {
      setBusy(false);
    }
  }

  async function evaluateCycle() {
    setBusy(true);
    try {
      const response = await fetch(`${API}/autonomous/evaluate`, { method: 'POST' });
      const data = await response.json();
      setStateSnapshot(data.state || null);
      if (data.decisions?.length) {
        setActions((prev) => [...data.decisions, ...prev].slice(0, 40));
      }
    } finally {
      setBusy(false);
    }
  }

  async function overrideAction(action, target, reason) {
    setBusy(true);
    try {
      const response = await fetch(`${API}/autonomous/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, target, reason, payload: { target, reason } }),
      });
      const data = await response.json();
      if (data.action) {
        setActions((prev) => [data.action, ...prev].slice(0, 40));
      }
      await loadState();
    } finally {
      setBusy(false);
    }
  }

  async function rollbackAction(actionId) {
    setBusy(true);
    try {
      await fetch(`${API}/autonomous/actions/${actionId}/rollback`, { method: 'POST' });
      await loadState();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: 'grid', gap: '0.9rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#94a3b8' }}>
          Autonomous Mode
        </h2>
        <p style={{ margin: '0.5rem 0 0', fontSize: 12, color: '#64748b' }}>
          Controle humano sobre o John Monolito: decisão, execução e rollback.
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
              border: `1px solid ${mode === item ? '#facc15' : '#334155'}`,
              background: mode === item ? '#1e293b' : '#020617',
              color: mode === item ? '#facc15' : '#cbd5e1',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            {item}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Receita</div>
          <strong style={{ color: '#22c55e', fontSize: 18 }}>{Math.round(stateSnapshot?.revenue || 0).toLocaleString('pt-BR')}</strong>
        </div>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Risco</div>
          <strong style={{ color: stateSnapshot?.risk_level === 'high' ? '#ef4444' : '#f59e0b', fontSize: 18 }}>{stateSnapshot?.risk_level || 'unknown'}</strong>
        </div>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Top monólito</div>
          <strong style={{ color: '#38bdf8', fontSize: 18 }}>{stateSnapshot?.top_monolith || 'unknown'}</strong>
        </div>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: '0.9rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase' }}>Gargalos</div>
          <strong style={{ color: '#f1f5f9', fontSize: 16 }}>{(stateSnapshot?.bottlenecks || []).join(', ') || 'nenhum'}</strong>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button type="button" onClick={evaluateCycle} disabled={busy} style={actionButtonStyle('#22c55e')}>
          Rodar ciclo autônomo
        </button>
        <button type="button" onClick={() => overrideAction('prioritize_legal', 'juridicotech', 'Override manual: fila jurídica')} disabled={busy} style={actionButtonStyle('#a855f7')}>
          Priorizar jurídico
        </button>
        <button type="button" onClick={() => overrideAction('boost_marketing', 'gamemkt', 'Override manual: conversão baixa')} disabled={busy} style={actionButtonStyle('#38bdf8')}>
          Acelerar marketing
        </button>
        <button type="button" onClick={() => overrideAction('reduce_exposure', 'all_monoliths', 'Override manual: proteger caixa')} disabled={busy} style={actionButtonStyle('#ef4444')}>
          Reduzir exposição
        </button>
      </div>

      <div style={{ display: 'grid', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
        {actions.slice(0, 12).map((item) => (
          <ActionRow key={item.id} item={item} onRollback={rollbackAction} />
        ))}
        {actions.length === 0 && <span style={{ fontSize: 12, color: '#64748b' }}>Nenhuma ação autônoma registrada.</span>}
      </div>
    </div>
  );
}

function actionButtonStyle(color) {
  return {
    padding: '0.6rem 0.85rem',
    borderRadius: 10,
    border: `1px solid ${color}66`,
    background: `${color}18`,
    color,
    cursor: 'pointer',
    fontSize: 11,
    fontWeight: 700,
  };
}
import { useEffect, useState } from 'react';
import { resolvedApiBaseUrl } from '@/services/runtimeConfig';

const API = resolvedApiBaseUrl;
const MODES = ['AUTO', 'SUPERVISED', 'MANUAL'];

function modeButtonStyle(active) {
  return {
    border: `1px solid ${active ? '#f5c542' : '#334155'}`,
    background: active ? '#1f2937' : '#0f172a',
    color: active ? '#f5c542' : '#cbd5e1',
    borderRadius: 8,
    padding: '6px 10px',
    fontSize: 12,
    cursor: 'pointer',
  };
}

export default function ExecutiveControl() {
  const [mode, setMode] = useState('SUPERVISED');
  const [busy, setBusy] = useState(false);
  const [warning, setWarning] = useState('');

  async function loadState() {
    try {
      const response = await fetch(`${API}/executive/state`);
      const data = await response.json();
      setMode(data.state?.mode || 'SUPERVISED');
    } catch (_error) {
      setWarning('Executive control offline');
    }
  }

  useEffect(() => {
    loadState();
  }, []);

  async function changeMode(nextMode) {
    if (nextMode === mode) return;
    setBusy(true);
    setWarning('');
    try {
      const response = await fetch(`${API}/executive/mode`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: nextMode }),
      });
      if (!response.ok) throw new Error('mode_update_failed');
      const data = await response.json();
      setMode(data.mode || nextMode);
    } catch (_error) {
      setWarning('Falha ao alterar modo executivo');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{
      background: '#000',
      color: '#f5c542',
      borderRadius: 12,
      border: '1px solid #1e293b',
      padding: '14px',
      display: 'grid',
      gap: 10,
    }}>
      <h2 style={{ margin: 0, fontSize: 16 }}>Executive Control</h2>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {MODES.map((item) => (
          <button
            key={item}
            type="button"
            disabled={busy}
            onClick={() => changeMode(item)}
            style={modeButtonStyle(mode === item)}
          >
            {item}
          </button>
        ))}
      </div>

      <p style={{ margin: 0, fontSize: 12, color: '#e2e8f0' }}>Modo atual: {mode}</p>

      <div style={{
        marginTop: 6,
        background: '#220a0a',
        border: '1px solid #7f1d1d',
        borderRadius: 8,
        padding: '8px 10px',
        color: '#fecaca',
        fontSize: 12,
      }}>
        Todas decisões passam por JuridicoTech + CEA antes de execução crítica.
      </div>

      {warning && <p style={{ margin: 0, fontSize: 12, color: '#f87171' }}>{warning}</p>}
    </div>
  );
}

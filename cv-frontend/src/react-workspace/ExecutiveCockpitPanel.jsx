import { useEffect, useState } from 'react';

export default function ExecutiveCockpitPanel() {
  const [trust, setTrust] = useState({});
  const [sensitivity, setSensitivity] = useState({});
  const [heatmap, setHeatmap] = useState({});

  useEffect(() => {
    async function load() {
      const res = await fetch('/control/executive_cockpit');
      const data = await res.json();
      setTrust(data.trust_scores || {});
      setSensitivity(data.sensitivity || {});
      setHeatmap(data.heatmap || {});
    }
    load();
  }, []);

  return (
    <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem', marginTop: 24 }}>
      <h2 style={{ color: '#facc15', fontSize: 16 }}>CEO Cockpit</h2>
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        <div>
          <strong>Trust Score</strong>
          <ul>
            {Object.entries(trust).map(([mod, score]) => (
              <li key={mod}><span style={{ color: '#38bdf8' }}>{mod}</span>: {score.toFixed(2)}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Sensibilidade</strong>
          <ul>
            {Object.entries(sensitivity).map(([mod, sens]) => (
              <li key={mod}><span style={{ color: '#f59e0b' }}>{mod}</span>: {sens.toFixed(2)}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Heatmap</strong>
          <ul>
            {Object.entries(heatmap).map(([mod, stats]) => (
              <li key={mod}><span style={{ color: '#22c55e' }}>{mod}</span>: {stats.length} dias de atividade</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

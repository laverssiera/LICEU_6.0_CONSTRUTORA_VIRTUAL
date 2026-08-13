import { useEffect, useState } from 'react';

export default function ChangeHeatmapPanel() {
  const [heatmap, setHeatmap] = useState(null);
  const [ranking, setRanking] = useState([]);

  useEffect(() => {
    async function loadHeatmap() {
      const res = await fetch('/control/change_heatmap');
      const data = await res.json();
      setHeatmap(data.heatmap);
      setRanking(data.ranking);
    }
    loadHeatmap();
  }, []);

  return (
    <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem', marginTop: 24 }}>
      <h2 style={{ color: '#facc15', fontSize: 16 }}>Change Heatmap</h2>
      <div style={{ marginBottom: 16 }}>
        <strong>Top mudanças/sensibilidade:</strong>
        <ul>
          {ranking.map(([mod, changes, failures, sens]) => (
            <li key={mod}>
              <span style={{ color: '#facc15' }}>{mod}</span> — {changes} mudanças, {failures} falhas, sensibilidade média: {sens.toFixed(2)}
            </li>
          ))}
        </ul>
      </div>
      <div style={{ maxHeight: 240, overflowY: 'auto' }}>
        {heatmap && Object.entries(heatmap).map(([mod, stats]) => (
          <div key={mod} style={{ marginBottom: 12 }}>
            <strong style={{ color: '#38bdf8' }}>{mod}</strong>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
              {stats.map((s) => (
                <span key={s.day} style={{
                  background: s.failures > 0 ? '#ef4444' : s.changes > 0 ? '#f59e0b' : '#22c55e',
                  color: '#fff', borderRadius: 4, padding: '2px 8px', fontSize: 11
                }}>
                  {s.day}: {s.changes} mudanças, {s.failures} falhas, sens: {s.sensitivity.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

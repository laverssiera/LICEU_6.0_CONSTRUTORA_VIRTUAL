import { useState } from 'react';
import { canManageWorkspace } from './accessControl';

export default function ChangeApprovalPanel({ user }) {
  const [proposals, setProposals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ author: '', description: '', dsl_text: '', tenant_id: '', pipelines: '' });
  const [simulation, setSimulation] = useState(null);
  const [audit, setAudit] = useState(null);
  const [status, setStatus] = useState('');

  async function loadProposals() {
    const res = await fetch('/control/change/list');
    setProposals(await res.json());
  }

  async function submitProposal(e) {
    e.preventDefault();
    setStatus('Enviando...');
    const resp = await fetch('/control/change/submit_proposal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...form,
        pipelines: form.pipelines.split(',').map((id) => ({ id: id.trim() })),
      }),
    });
    setStatus('Proposta enviada!');
    loadProposals();
  }

  async function simulateImpact(proposal_id) {
    setStatus('Simulando...');
    const resp = await fetch('/control/change/simulate_impact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposal_id }),
    });
    setSimulation(await resp.json());
    setStatus('');
  }

  async function approve(proposal_id) {
    const approver = prompt('Aprovador:');
    const justification = prompt('Justificativa:');
    await fetch('/control/change/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposal_id, approver, justification }),
    });
    loadProposals();
  }

  async function apply(proposal_id) {
    await fetch('/control/change/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposal_id }),
    });
    loadProposals();
  }

  async function rollback(proposal_id) {
    await fetch('/control/change/rollback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposal_id }),
    });
    loadProposals();
  }

  async function showAudit(proposal_id) {
    const resp = await fetch(`/control/change/audit?proposal_id=${proposal_id}`);
    setAudit(await resp.json());
  }

  if (!canManageWorkspace(user)) {
    return (
      <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem', marginTop: 24, color: '#64748b' }}>
        <h2 style={{ color: '#facc15', fontSize: 16 }}>Aprovação de Mudanças</h2>
        <div>Você não tem permissão para acessar este painel.</div>
      </div>
    );
  }
  return (
    <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: 18, padding: '1.2rem', marginTop: 24 }}>
      <h2 style={{ color: '#facc15', fontSize: 16 }}>Aprovação de Mudanças</h2>
      <button onClick={loadProposals} style={{ marginBottom: 12 }}>Carregar propostas</button>
      <form onSubmit={submitProposal} style={{ display: 'grid', gap: 8, marginBottom: 16 }}>
        <input required placeholder="Autor" value={form.author} onChange={e => setForm(f => ({ ...f, author: e.target.value }))} />
        <input required placeholder="Descrição" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        <textarea required placeholder="Regra DSL" value={form.dsl_text} onChange={e => setForm(f => ({ ...f, dsl_text: e.target.value }))} />
        <input required placeholder="Tenant ID" value={form.tenant_id} onChange={e => setForm(f => ({ ...f, tenant_id: e.target.value }))} />
        <input required placeholder="IDs dos pipelines (separados por vírgula)" value={form.pipelines} onChange={e => setForm(f => ({ ...f, pipelines: e.target.value }))} />
        <button type="submit">Submeter proposta</button>
      </form>
      {status && <div style={{ color: '#22c55e', marginBottom: 8 }}>{status}</div>}
      <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 12 }}>
        {proposals.map((p) => (
          <div key={p.proposal_id} style={{ borderBottom: '1px solid #1e293b', padding: 8 }}>
            <strong>{p.description}</strong> <span style={{ color: '#94a3b8' }}>({p.status})</span>
            <button onClick={() => simulateImpact(p.proposal_id)} style={{ marginLeft: 8 }}>Simular</button>
            <button onClick={() => approve(p.proposal_id)} style={{ marginLeft: 8 }}>Aprovar</button>
            <button onClick={() => apply(p.proposal_id)} style={{ marginLeft: 8 }}>Aplicar</button>
            <button onClick={() => rollback(p.proposal_id)} style={{ marginLeft: 8 }}>Rollback</button>
            <button onClick={() => showAudit(p.proposal_id)} style={{ marginLeft: 8 }}>Auditoria</button>
          </div>
        ))}
      </div>
      {simulation && (
        <div style={{ background: '#1e293b', color: '#f1f5f9', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <strong>Simulação de Impacto:</strong>
          <pre>{JSON.stringify(simulation, null, 2)}</pre>
        </div>
      )}
      {audit && (
        <div style={{ background: '#1e293b', color: '#f1f5f9', padding: 12, borderRadius: 8 }}>
          <strong>Auditoria:</strong>
          <pre>{JSON.stringify(audit, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

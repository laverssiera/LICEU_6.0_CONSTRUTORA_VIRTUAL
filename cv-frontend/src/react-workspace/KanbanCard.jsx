export default function KanbanCard({ card }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-3 shadow">
      <h4 className="text-sm font-semibold text-slate-100">{card.title}</h4>
      <p className="mt-1 text-xs text-slate-400">{card.entity_type || 'entity'}</p>
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="rounded bg-slate-800 px-2 py-1 text-slate-200">{card.stage}</span>
        <span className="text-amber-300">Risco: {card.risk || 'unknown'}</span>
      </div>
    </div>
  );
}

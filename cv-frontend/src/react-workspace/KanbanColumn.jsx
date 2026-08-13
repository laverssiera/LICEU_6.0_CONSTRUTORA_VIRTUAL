import KanbanCard from './KanbanCard';

export default function KanbanColumn({ title, cards }) {
  return (
    <section className="min-w-72 rounded-xl border border-slate-800 bg-slate-950/70 p-3">
      <header className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">{title}</h3>
        <span className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">{cards.length}</span>
      </header>

      <div className="grid gap-2">
        {cards.map((card) => (
          <KanbanCard key={card.id} card={card} />
        ))}
      </div>
    </section>
  );
}

export default function JohnPanel({ cards }) {
  return (
    <aside className="h-full border-l border-slate-800 bg-slate-950 p-4">
      <h3 className="text-sm font-bold text-cyan-300">JOHN AI</h3>
      <p className="mt-1 text-xs text-slate-400">Sugestoes de acao em tempo real</p>

      <div className="mt-4 grid gap-3">
        {cards.slice(0, 5).map((card) => (
          <div key={card.id} className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-sm">
            <p className="font-medium text-slate-100">{card.title}</p>
            <p className="mt-1 text-xs text-emerald-300">Sugerido: priorizar contato</p>
          </div>
        ))}
      </div>
    </aside>
  );
}

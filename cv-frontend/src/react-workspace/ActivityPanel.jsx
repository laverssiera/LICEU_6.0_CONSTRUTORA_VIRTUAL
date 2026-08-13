export default function ActivityPanel({ activityLog }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/80 p-3">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Activity</h4>
      <div className="mt-3 max-h-40 overflow-y-auto">
        {activityLog.map((row) => (
          <div key={row.id} className="border-b border-slate-800 py-2 text-xs text-slate-300">
            <div>{row.eventType}</div>
            <div className="text-slate-500">{row.cardId}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

import { useMemo, useState } from 'react';
import useEventBus from './useEventBus';
import { handleEvent } from './eventHandler';
import { canViewCard, canManageWorkspace, getMenuByRole } from './accessControl';
import KanbanColumn from './KanbanColumn';
import JohnPanel from './JohnPanel';
import ActivityPanel from './ActivityPanel';

const stages = ['leads', 'negotiation', 'proposal', 'juridico', 'closed'];

const defaultUser = {
  id: 'irmandade_demo',
  role: 'SUPER_ADMIN',
  name: 'Operacao LICEU',
};

export default function KanbanBoard() {
  const [cards, setCards] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [workspaceName] = useState('LICEU 6.0 Central Workspace');
  const user = defaultUser;
  const roleMenu = getMenuByRole(user);

  useEventBus((event) => handleEvent(event, setCards, setActivityLog));

  const visibleCards = useMemo(
    () => cards.filter((card) => canViewCard(user, card)),
    [cards, user]
  );

  const kpis = useMemo(() => {
    const total = visibleCards.length;
    const closed = visibleCards.filter((card) => card.stage === 'closed').length;
    const highRisk = visibleCards.filter((card) => card.risk === 'high').length;
    const conversion = total > 0 ? ((closed / total) * 100).toFixed(1) : '0.0';
    return { total, closed, highRisk, conversion };
  }, [visibleCards]);

  return (
    <div className="h-screen bg-slate-950 text-slate-100">
      <header className="grid grid-cols-12 border-b border-slate-800 bg-slate-900/80 px-4 py-3">
        <div className="col-span-6">
          <p className="text-xs uppercase tracking-widest text-cyan-300">Trading Desk</p>
          <h1 className="text-lg font-semibold">{workspaceName}</h1>
        </div>
        <div className="col-span-6 grid grid-cols-4 gap-2 text-xs">
          <div className="rounded bg-slate-800 p-2">Cards: {kpis.total}</div>
          <div className="rounded bg-slate-800 p-2">Closed: {kpis.closed}</div>
          <div className="rounded bg-slate-800 p-2">High Risk: {kpis.highRisk}</div>
          <div className="rounded bg-slate-800 p-2">Conv: {kpis.conversion}%</div>
        </div>
      </header>

      <main className="grid h-[calc(100vh-68px)] grid-cols-12">
        <aside className="col-span-2 border-r border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Workspace</h2>
          <ul className="mt-3 grid gap-2 text-sm text-slate-300">
            {roleMenu.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-slate-500">Permissao de gestao: {canManageWorkspace(user) ? 'sim' : 'nao'}</p>
        </aside>

        <section className="col-span-7 overflow-x-auto p-4">
          <div className="grid grid-flow-col auto-cols-[18rem] gap-3">
            {stages.map((stage) => (
              <KanbanColumn
                key={stage}
                title={stage}
                cards={visibleCards.filter((card) => card.stage === stage)}
              />
            ))}
          </div>

          <div className="mt-4">
            <ActivityPanel activityLog={activityLog} />
          </div>
        </section>

        <section className="col-span-3">
          <JohnPanel cards={visibleCards} />
        </section>
      </main>
    </div>
  );
}

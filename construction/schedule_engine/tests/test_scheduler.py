from construction_layer.domain.product_node import ProductNode
from construction.schedule_engine.convert import traverse_product_tree
from construction.schedule_engine.dependencies import apply_dependencies
from construction.schedule_engine.scheduler import Scheduler
from construction.schedule_engine.financial import financial_curve, cumulative_curve

def test_scheduler_basic():
    # Mock simples de ProductNode
    class MockNode:
        def __init__(self, id, name, cost, time, children=None):
            self.id = id
            self.name = name
            self._cost = cost
            self._time = time
            self.children = children or []
        def total_cost(self):
            return self._cost
        def total_time(self):
            return self._time
    root = MockNode('1', 'Fundacao', 1000, 16)
    estrutura = MockNode('2', 'Estrutura', 2000, 24)
    alvenaria = MockNode('3', 'Alvenaria', 1500, 20)
    acabamento = MockNode('4', 'Acabamento', 1200, 12)
    root.children = [estrutura]
    estrutura.children = [alvenaria]
    alvenaria.children = [acabamento]
    tasks = traverse_product_tree(root)
    apply_dependencies(tasks)
    scheduler = Scheduler(tasks)
    scheduled = scheduler.calculate()
    timeline = financial_curve(scheduled)
    s_curve = cumulative_curve(timeline)
    from runtime.testing.consistency.deterministic_assert import deterministic_assert
    deterministic_assert(scheduled[0].start_day, 0)
    assert scheduled[-1].end_day > 0
    deterministic_assert(sum(t.cost for t in scheduled), 5700)
    deterministic_assert(max(s_curve.values()), 5700)

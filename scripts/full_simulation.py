"""
Script de simulação ponta a ponta do pipeline LICEU 6.0
- BIM → Product Tree → Construction Layer → Schedule Engine → Financial Engine → EventBus (Kernel)
"""
import asyncio
from construction_layer.domain.product_node import ProductNode
from construction.schedule_engine.convert import traverse_product_tree
from construction.schedule_engine.dependencies import apply_dependencies
from construction.schedule_engine.scheduler import Scheduler
from construction.schedule_engine.financial import financial_curve, cumulative_curve
from construction.schedule_engine.send_to_kernel import send_schedule_to_kernel

# Mock simples de entrada BIM
input_data = {
    "walls": [
        {"type": "alvenaria", "area": 120},
        {"type": "alvenaria", "area": 80}
    ],
    "slabs": [
        {"type": "laje", "area": 100}
    ],
    "finishes": [
        {"type": "pintura", "area": 200}
    ]
}

# Ajuste para ProductNode mockado
class ProductNode:
    def __init__(self, id, name, children=None):
        self.id = id
        self.name = name
        self.children = children or []
        self._cost = 0
        self._time = 0
    def total_cost(self):
        total = getattr(self, '_cost', 0)
        for child in self.children:
            total += child.total_cost()
        return total
    def total_time(self):
        total = getattr(self, '_time', 0)
        for child in self.children:
            total += child.total_time()
        return total

def bim_pipeline(input_data):
    # Simula BIM Engine → Product Tree
    # Aqui você usaria o BIM real, mas vamos mockar um ProductNode
    root = ProductNode(id="root", name="Casa", children=[])
    for i, wall in enumerate(input_data["walls"]):
        node = ProductNode(id=f"wall{i}", name="Alvenaria", children=[])
        node._cost = wall["area"] * 100  # mock
        node._time = wall["area"] * 0.2  # mock
        root.children.append(node)
    for i, slab in enumerate(input_data["slabs"]):
        node = ProductNode(id=f"slab{i}", name="Laje", children=[])
        node._cost = slab["area"] * 150
        node._time = slab["area"] * 0.3
        root.children.append(node)
    for i, finish in enumerate(input_data["finishes"]):
        node = ProductNode(id=f"finish{i}", name="Pintura", children=[])
        node._cost = finish["area"] * 50
        node._time = finish["area"] * 0.1
        root.children.append(node)
    return root

def main():
    # 1. BIM → Product Tree
    product_tree = bim_pipeline(input_data)
    # 2. Construction Layer (custo/prazo)
    cost = product_tree.total_cost()
    time = product_tree.total_time()
    print(f"Custo total: R$ {cost:.2f}")
    print(f"Prazo total: {time:.2f} horas")
    # 3. Schedule Engine
    tasks = traverse_product_tree(product_tree)
    apply_dependencies(tasks)
    scheduler = Scheduler(tasks)
    scheduled = scheduler.calculate()
    # 4. Financial Engine
    timeline = financial_curve(scheduled)
    s_curve = cumulative_curve(timeline)
    print(f"Curva financeira (dias): {timeline}")
    print(f"Curva S acumulada: {s_curve}")
    # 5. Envia evento para o Kernel
    asyncio.run(send_schedule_to_kernel(scheduled, product_id=product_tree.id))

if __name__ == "__main__":
    main()

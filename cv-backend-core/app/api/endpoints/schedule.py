from fastapi import APIRouter, Body
from construction.schedule_engine.convert import traverse_product_tree
from construction.schedule_engine.dependencies import apply_dependencies
from construction.schedule_engine.scheduler import Scheduler
from construction.schedule_engine.financial import financial_curve, cumulative_curve
from construction.schedule_engine.send_to_kernel import send_schedule_to_kernel
import asyncio

router = APIRouter()

@router.post("/schedule/generate")
def generate_schedule(product_tree: dict = Body(...)):
    # Espera-se que o frontend envie a árvore de produtos como dict
    # Reconstrói ProductNode
    def dict_to_node(d):
        node = type("ProductNode", (), {})()
        node.id = d.get("id")
        node.name = d.get("name")
        node.children = [dict_to_node(c) for c in d.get("children", [])]
        node._cost = d.get("_cost", 0)
        node._time = d.get("_time", 0)
        node.total_cost = lambda: node._cost + sum(c.total_cost() for c in node.children)
        node.total_time = lambda: node._time + sum(c.total_time() for c in node.children)
        return node
    root = dict_to_node(product_tree)
    tasks = traverse_product_tree(root)
    apply_dependencies(tasks)
    scheduler = Scheduler(tasks)
    scheduled = scheduler.calculate()
    timeline = financial_curve(scheduled)
    s_curve = cumulative_curve(timeline)
    # Envia evento ao Kernel (assíncrono)
    asyncio.create_task(send_schedule_to_kernel(scheduled, product_id=root.id))
    return {
        "cost": root.total_cost(),
        "time": root.total_time(),
        "schedule": [t.__dict__ for t in scheduled],
        "finance": timeline,
        "s_curve": s_curve
    }

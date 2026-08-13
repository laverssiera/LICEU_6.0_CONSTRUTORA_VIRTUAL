from construction_layer.domain.product_node import ProductNode
from .task import Task

def node_to_task(node: ProductNode):
    duration_days = node.total_time() / 8  # 8h/dia
    return Task(
        id=node.id,
        name=node.name,
        duration_days=duration_days,
        cost=node.total_cost(),
        dependencies=[]
    )

def traverse_product_tree(node: ProductNode, tasks=None):
    if tasks is None:
        tasks = []
    tasks.append(node_to_task(node))
    for child in node.children:
        traverse_product_tree(child, tasks)
    return tasks

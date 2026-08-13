from construction_layer.domain.product_node import ProductNode
from .convert import traverse_product_tree
from .dependencies import apply_dependencies
from .scheduler import Scheduler
from .financial import financial_curve, cumulative_curve
from .send_to_kernel import send_schedule_to_kernel
import asyncio

# Exemplo de uso
# product_tree = ... (instanciar ProductNode raiz)
# tasks = traverse_product_tree(product_tree)
# apply_dependencies(tasks)
# scheduler = Scheduler(tasks)
# scheduled_tasks = scheduler.calculate()
# timeline = financial_curve(scheduled_tasks)
# s_curve = cumulative_curve(timeline)

# Exemplo de integração com o Kernel/EventBus
# asyncio.run(send_schedule_to_kernel(scheduled_tasks, product_id=product_tree.id))
# O evento será impresso no console (substitua pelo EventBus real para produção)

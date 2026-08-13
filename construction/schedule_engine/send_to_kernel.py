import asyncio
from .event import build_schedule_event
from stream_bus.nats_wrapper import EventBus

async def send_schedule_to_kernel(tasks, product_id=None, tenant=None, correlation_id=None, decision_id=None):
    event = build_schedule_event(tasks, product_id, tenant, correlation_id, decision_id)
    bus = EventBus()
    await bus.connect()
    await bus.publish("construction.schedule.generated", event)
    print("Evento de cronograma enviado ao Kernel:", event)

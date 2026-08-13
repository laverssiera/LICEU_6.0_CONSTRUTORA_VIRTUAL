import asyncio
from construction_layer.services.build_event import build_event
#from stream_bus.event_bus import EventBus  # Supondo que exista

async def send_to_kernel(product_node):
    # bus = EventBus()
    # await bus.connect()
    event = build_event(product_node)
    # await bus.publish("construction.product.calculated", event)
    print("Evento enviado ao Kernel:", event)

# Exemplo de uso:
#if __name__ == "__main__":
#    from construction_layer.use_cases.simulate_wall_v2 import parede
#    asyncio.run(send_to_kernel(parede))

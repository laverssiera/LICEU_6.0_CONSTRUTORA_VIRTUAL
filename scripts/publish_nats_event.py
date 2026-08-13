import asyncio
import json
from nats.aio.client import Client as NATS

async def main():
    nc = NATS()
    await nc.connect("nats://localhost:4222")

    # Exemplo de evento
    event = {
        "monolith": "ARCHIMEDES",
        "event": "housing.created",
        "payload": {
            "id": 123,
            "city": "São Paulo",
            "value": 1000000
        }
    }

    await nc.publish(
        "ecosystem.event",
        json.dumps(event).encode()
    )
    print("Evento publicado em ecosystem.event!")
    await nc.drain()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os

from sdk.event_bus import EventBus


async def run() -> None:
    nats_url = os.getenv("NATS_PUBLIC_URL", "nats://localhost:4222")
    bus = EventBus(nats_url=nats_url)
    await bus.publish("system.boot", {"stage": "local-bootstrap"}, source="core-sdk")
    print(f"evento system.boot publicado em liceu.events via {nats_url}")
    await bus.close()


if __name__ == "__main__":
    asyncio.run(run())

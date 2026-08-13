import asyncio
import os

from sdk.event_bus import EventBus


async def run() -> None:
    nats_url = os.getenv("NATS_PUBLIC_URL", "nats://localhost:4222")
    bus = EventBus(nats_url=nats_url)

    lead_payload = {
        "lead_id": "lead-001",
        "origin": "archimedes",
        "segment": "alto_padrao",
    }
    deal_payload = {
        "deal_id": "deal-001",
        "lead_id": "lead-001",
        "property_id": "prop-001",
    }

    await bus.publish("lead.created", lead_payload, source="archimedes")
    await bus.publish("deal.closed", deal_payload, source="archimedes")
    print(f"fluxo de demo publicado em liceu.events via {nats_url}")
    await bus.close()


if __name__ == "__main__":
    asyncio.run(run())
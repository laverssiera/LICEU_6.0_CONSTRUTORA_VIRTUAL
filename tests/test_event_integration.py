# Teste de integração por evento
import pytest
import asyncio
# from liceu_6_0.core_sdk.sdk.event_bus import EventBus

@pytest.mark.asyncio
async def test_publish_and_consume_event():
    bus = EventBus()
    received = {}
    async def handler(event):
        received.update(event)
    await bus.connect()
    await bus.subscribe_event(handler)
    await bus.publish_event(
        event_type="lead.created",
        payload={"lead_id": "123", "name": "João", "email": "joao@exemplo.com"},
        source="test",
        version="v1",
        correlation_id="corr-1"
    )
    await asyncio.sleep(1)
    assert received.get("type") == "lead.created"
    assert received.get("payload", {}).get("lead_id") == "123"

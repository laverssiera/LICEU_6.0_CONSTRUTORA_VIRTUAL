# Teste de carga no NATS
import asyncio
import time
import pytest
# from liceu_6_0.core_sdk.sdk.event_bus import EventBus

@pytest.mark.asyncio
async def test_nats_load():
    bus = EventBus()
    await bus.connect()
    total = 1000
    start = time.time()
    for i in range(total):
        await bus.publish_event(
            event_type="lead.created",
            payload={"lead_id": str(i), "name": f"User{i}", "email": f"user{i}@exemplo.com"},
            source="loadtest",
            version="v1",
            correlation_id=f"corr-{i}"
        )
    elapsed = time.time() - start
    print(f"Enviados {total} eventos em {elapsed:.2f}s ({total/elapsed:.1f} eventos/s)")

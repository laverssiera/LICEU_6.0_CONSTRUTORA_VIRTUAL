# DLQ Publisher centralizado
from liceu-6.0.core-sdk.sdk.event_bus import EventBus
from datetime import datetime
import asyncio

async def publish_dlq(event, reason, source="runtime"):
    bus = EventBus()
    await bus.connect()
    tenant_id = event.get("tenant_id") or event.get("payload", {}).get("tenant_id")
    if not tenant_id:
        raise ValueError("DLQ: Evento sem tenant_id (obrigatório para isolamento multi-tenant)")
    payload = {
        "event": event,
        "reason": reason,
        "pipeline_id": event.get("pipeline_id") or event.get("payload", {}).get("pipeline_id"),
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat(),
        "source": source
    }
    await bus.nc.publish("liceu.events.dlq", str(payload).encode())
    print(f"[DLQ] Evento enviado para DLQ: {payload}")

if __name__ == "__main__":
    asyncio.run(publish_dlq({"type": "invalid.event", "payload": {"pipeline_id": "p1"}}, "INVALID_STAGE_TRANSITION", source="hubbackoffice"))

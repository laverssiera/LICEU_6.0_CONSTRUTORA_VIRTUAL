# Integração Kanban ↔ Auditoria: finding automático
from liceu-6.0.core-sdk.sdk.event_bus import EventBus
import asyncio

def gerar_finding(pipeline_id, motivo, stage=None):
    payload = {
        "pipeline_id": pipeline_id,
        "motivo": motivo,
        "stage": stage
    }
    asyncio.run(_emit_finding(payload))

async def _emit_finding(payload):
    bus = EventBus()
    await bus.connect()
    await bus.publish_event(
        event_type="audit.finding",
        payload=payload,
        source="kanban",
        version="v1",
        correlation_id=payload["pipeline_id"]
    )

if __name__ == "__main__":
    gerar_finding("pipeline-1", motivo="travado", stage="VIABILIDADE_FINANCEIRA")

# SAGA Engine — Orquestração e Compensação de Transações Distribuídas
from runtime.event_store import persist_event
from datetime import datetime

# Definição de compensações para eventos financeiros
SAGA_COMPENSATIONS = {
    "payment.generated": [
        {"type": "commission.cancelled"},
        {"type": "pipeline.mark_inconsistent"}
    ],
    # Adicione outros eventos e compensações conforme necessário
}

def saga_compensate(event, reason="SAGA_COMPENSATION_TRIGGERED"):
    """
    Executa compensações lógicas para um evento financeiro que falhou.
    Gera eventos de compensação e persiste no event_store.
    """
    pipeline_id = event.get("pipeline_id")
    tenant_id = event.get("tenant_id")
    correlation_id = event.get("correlation_id")
    compensations = SAGA_COMPENSATIONS.get(event["type"], [])
    for comp in compensations:
        comp_event = {
            "id": f"comp-{event['id']}-{comp['type']}",
            "type": comp["type"],
            "version": "v1",
            "source": "saga_engine",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "pipeline_id": pipeline_id,
                "reason": reason,
                "original_event": event["id"]
            },
            "tenant_id": tenant_id,
            "correlation_id": correlation_id
        }
        persist_event(comp_event)
        print(f"[SAGA] Compensação emitida: {comp_event}")

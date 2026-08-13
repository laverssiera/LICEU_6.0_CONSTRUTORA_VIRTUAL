import json
from datetime import datetime
import uuid
from .task import Task

def build_schedule_event(tasks, product_id=None, tenant=None, correlation_id=None, decision_id=None):
    """
    Gera um evento compatível com o EventEnvelope do CORE-DNA para o cronograma físico-financeiro.
    """
    payload = {
        "product_id": product_id,
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "start_day": t.start_day,
                "end_day": t.end_day,
                "duration_days": t.duration_days,
                "cost": t.cost,
                "dependencies": t.dependencies
            } for t in tasks
        ]
    }
    return {
        "id": str(uuid.uuid4()),
        "type": "construction.schedule.generated",
        "version": "v1",
        "source": "schedule_engine",
        "timestamp": datetime.utcnow().isoformat(),
        "tenant": tenant or "default",
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "payload": json.dumps(payload),
        "decision_id": decision_id or ""
    }

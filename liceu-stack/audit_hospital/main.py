from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="Audit Hospital")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "alerts": [],
    "health_score": 92,
    "events": [],
}


def _push_event(event_type: str, payload: dict, source: str = "audit_hospital"):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    STATE["events"].append(event)
    if len(STATE["events"]) > 500:
        STATE["events"] = STATE["events"][-500:]
    return event


@app.on_event("startup")
async def setup():
    if not nc.is_connected:
        await nc.connect(NATS_URL)

    async def approved_handler(msg):
        data = json.loads(msg.data.decode())
        print(f"[audit_hospital] Auditoria iniciada para business_id={data.get('business_id')}")
        _push_event("audit.monitoring.started", {"business_id": data.get("business_id")})

    async def task_handler(msg):
        data = json.loads(msg.data.decode())
        if data.get("error_detected"):
            print(f"[audit_hospital] Issue detectado em project_id={data.get('project_id')}")
            alert = {
                "id": str(uuid.uuid4()),
                "severity": "high",
                "message": f"Issue detectado no projeto {data.get('project_id')}",
                "source": "audit_hospital",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            STATE["alerts"].append(alert)
            await nc.publish(
                "audit.issue",
                json.dumps({"project_id": data.get("project_id"), "reason": data.get("error_reason", "unknown")}).encode(),
            )
            _push_event("audit.issue.detected", {"project_id": data.get("project_id"), "reason": data.get("error_reason", "unknown")})

    await nc.subscribe("business.approved", cb=approved_handler)
    await nc.subscribe("operation.task.completed", cb=task_handler)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "audit_hospital"}


@app.get("/state/alerts")
def state_alerts(limit: int = 20):
    safe_limit = max(1, min(limit, 200))
    items = STATE["alerts"][-safe_limit:]
    return {"items": items, "total": len(STATE["alerts"]), "health_score": STATE["health_score"]}


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}


@app.post("/actions/trigger-audit/{project_id}")
async def trigger_audit(project_id: str):
    alert = {
        "id": str(uuid.uuid4()),
        "severity": "high",
        "message": f"Auditoria acionada para {project_id}",
        "source": "audit_hospital",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    STATE["alerts"].append(alert)
    await nc.publish("audit.issue", json.dumps({"project_id": project_id, "reason": "manual_trigger"}).encode())
    event = _push_event("audit.issue.detected", {"project_id": project_id, "reason": "manual_trigger"})
    return {"status": "triggered", "alert": alert, "event": event}

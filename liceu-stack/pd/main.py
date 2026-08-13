from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="P&D")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "process_updates": [],
    "events": [],
}


def _push_event(event_type: str, payload: dict, source: str = "pd"):
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

    async def handler(msg):
        data = json.loads(msg.data.decode())
        print(f"[pd] Processo atualizado para project_id={data.get('project_id')}")
        update = {
            "id": str(uuid.uuid4()),
            "project_id": data.get("project_id"),
            "change": f"Padrao revisado por auditoria: {data.get('reason', 'n/a')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        STATE["process_updates"].append(update)
        _push_event("pd.process.updated", {"project_id": data.get("project_id")})

    await nc.subscribe("audit.issue", cb=handler)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "pd"}


@app.get("/state/processes")
def state_processes(limit: int = 20):
    safe_limit = max(1, min(limit, 200))
    items = STATE["process_updates"][-safe_limit:]
    return {"items": items, "total": len(STATE["process_updates"])}


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}


@app.post("/actions/start-training/{project_id}")
async def start_training(project_id: str):
    await nc.publish("academy.training.created", json.dumps({"project_id": project_id}).encode())
    event = _push_event("academy.training.created", {"project_id": project_id}, source="academy")
    return {"status": "started", "project_id": project_id, "event": event}

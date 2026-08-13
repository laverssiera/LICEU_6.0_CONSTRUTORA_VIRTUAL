from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="Fornecedores")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "requests": [],
    "events": [],
}


def _push_event(event_type: str, payload: dict):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": "fornecedores",
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
        print(f"[fornecedores] Material solicitado para project_id={data.get('project_id')}")
        request = {
            "id": str(uuid.uuid4()),
            "project_id": data.get("project_id"),
            "material": "kit_estrutura",
            "status": "requested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        STATE["requests"].append(request)
        _push_event("supply.material.requested", {"project_id": data.get("project_id")})

    await nc.subscribe("project.created", cb=handler)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "fornecedores"}


@app.get("/state/supply")
def state_supply(limit: int = 20):
    safe_limit = max(1, min(limit, 200))
    items = STATE["requests"][-safe_limit:]
    return {"items": items, "total": len(STATE["requests"])}


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}

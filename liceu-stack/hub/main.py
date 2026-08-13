from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="HUB")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "finance": {
        "dre": {"revenue": 3200000, "cost": 2000000, "expenses": 150000},
        "cash_flow": {"inflow": 3200000, "outflow": 2150000},
        "roi": 1.6,
    },
    "events": [],
}


def _push_event(event_type: str, payload: dict):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": "hub",
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
        print(f"[hub] Financeiro ativado para business_id={data.get('business_id')}")
        _push_event("finance.cost.recorded", {"business_id": data.get("business_id")})

    await nc.subscribe("business.approved", cb=handler)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "hub"}


@app.get("/state/finance")
def state_finance():
    return STATE["finance"]


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}


@app.post("/actions/release-payment/{project_id}")
async def release_payment(project_id: str):
    event = _push_event("finance.payment.released", {"project_id": project_id})
    await nc.publish("finance.payment.released", json.dumps({"project_id": project_id}).encode())
    return {"status": "released", "project_id": project_id, "event": event}

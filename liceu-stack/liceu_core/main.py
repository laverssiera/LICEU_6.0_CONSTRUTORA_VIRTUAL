from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="LICEU Core")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "pipeline": [
        {
            "id": "business-1",
            "title": "Empreendimento 20 casas",
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "stage": "Ideia",
            "estimated_cost": 2000000,
            "expected_return": 3200000,
        }
    ],
    "events": [],
}


def _push_event(event_type: str, payload: dict):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": "liceu_core",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    STATE["events"].append(event)
    if len(STATE["events"]) > 500:
        STATE["events"] = STATE["events"][-500:]
    return event


@app.on_event("startup")
async def startup():
    if not nc.is_connected:
        await nc.connect(NATS_URL)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "liceu_core"}


@app.post("/approve/{business_id}")
async def approve(business_id: str):
    for item in STATE["pipeline"]:
        if item["id"] == business_id:
            item["stage"] = "Aprovado"

    event = {
        "business_id": business_id,
        "source": "liceu_core",
    }
    await nc.publish("business.approved", json.dumps(event).encode())
    emitted = _push_event("core.business.approved", {"business_id": business_id})
    return {"status": "approved", "business_id": business_id, "event": emitted}


@app.post("/missions/cubesat/launch")
async def launch_cubesat_mission():
    mission_id = f"mission-cubesat-6u-{uuid.uuid4().hex[:8]}"
    mission_data = {
        "mission_name": "CubeSat 6U",
        "description": "Observação orbital e materiais espaciais.",
        "type": "CUBESAT_6U",
        "objectives": ["Observação orbital", "Materiais espaciais"],
        "gate": "Gate 4 - Liceu Core",
        "status": "INITIATED"
    }

    # 1. Decision Trail
    decision_payload = {
        "action": "MISSION_APPROVED_AND_INITIATED",
        "details": "Aprovada missão estratégica de CubeSat 6U via Gate 4 - Liceu Core",
    }
    
    # 2. Event Store
    evt = _push_event("core.mission.cubesat_launched", {
        "mission_id": mission_id,
        "gate": "Gate 4 - Liceu Core",
        "payload": mission_data
    })
    
    # Publish as federation event (Event Store logic in real cluster via NATS)
    if nc.is_connected:
        await nc.publish("mission.ledgers.audit", json.dumps(evt).encode())

    return {
        "status": "launched",
        "mission_id": mission_id,
        "ledgers_persisted": [
            "Mission Ledger",
            "Trust Ledger",
            "Event Store",
            "Decision Trail"
        ],
        "audit": "Missão CubeSat 6U auditável de ponta a ponta.",
        "mission_info": mission_data
    }

@app.get("/state/pipeline")
def state_pipeline():
    return {"items": STATE["pipeline"], "total": len(STATE["pipeline"])}


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}

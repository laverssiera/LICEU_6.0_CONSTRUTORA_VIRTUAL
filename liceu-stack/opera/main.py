from fastapi import FastAPI
from nats.aio.client import Client as NATS
import json
import os
from datetime import datetime, timezone
import uuid

app = FastAPI(title="OPERA")
nc = NATS()
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

STATE = {
    "projects": [],
    "events": [],
}


def _push_event(event_type: str, payload: dict):
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "source": "opera",
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
        business_id = data.get("business_id")
        project_id = f"project-{business_id}"
        project = {
            "id": project_id,
            "business_id": business_id,
            "name": f"Obra {business_id}",
            "status": "active",
            "progress": 10,
            "tasks_open": 3,
        }
        if next((p for p in STATE["projects"] if p["id"] == project_id), None) is None:
            STATE["projects"].append(project)
        print(f"[opera] Projeto criado para business_id={business_id}")
        await nc.publish(
            "project.created",
            json.dumps({"business_id": business_id, "project_id": project_id, "source": "opera"}).encode(),
        )
        _push_event("operation.project.created", {"business_id": business_id, "project_id": project_id})

    await nc.subscribe("business.approved", cb=handler)


@app.on_event("shutdown")
async def shutdown():
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health():
    return {"status": "ok", "service": "opera"}


@app.get("/state/projects")
def state_projects():
    return {"items": STATE["projects"], "total": len(STATE["projects"])}


@app.get("/state/events")
def state_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {"items": STATE["events"][-safe_limit:], "total": len(STATE["events"])}


@app.post("/actions/pause/{project_id}")
async def pause_project(project_id: str):
    project = next((item for item in STATE["projects"] if item["id"] == project_id), None)
    if project is None:
        return {"status": "not_found", "project_id": project_id}
    project["status"] = "paused"
    event = _push_event("operation.project.paused", {"project_id": project_id})
    await nc.publish("operation.project.paused", json.dumps({"project_id": project_id}).encode())
    return {"status": "paused", "project": project, "event": event}


@app.post("/actions/reinforce-team/{project_id}")
async def reinforce_team(project_id: str):
    project = next((item for item in STATE["projects"] if item["id"] == project_id), None)
    if project is None:
        return {"status": "not_found", "project_id": project_id}

    project["status"] = "active"
    project["tasks_open"] = max(0, int(project.get("tasks_open", 0)) - 1)
    project["progress"] = min(100, int(project.get("progress", 0)) + 8)

    event = _push_event("operation.team.reinforced", {"project_id": project_id})
    await nc.publish(
        "operation.team.reinforced",
        json.dumps({"project_id": project_id, "source": "opera"}).encode(),
    )
    return {"status": "reinforced", "project": project, "event": event}

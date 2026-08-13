from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime

router = APIRouter()

class FederationEventRegistry:
    """
    Catálogo central de eventos federais.
    Responsável por garantir que validação e publicação de eventos ocorram com governança antes 
    de irem para o Event Store.
    """
    def __init__(self):
        self.events = {}
        # Pre-seed com eventos vitais
        event_names = [
            "MISSION_CREATED", "MISSION_APPROVED", "MISSION_EXECUTED",
            "DIGITAL_TWIN_UPDATED", "SATELLITE_INSPECTED", "NUCLEUS_SIMULATED",
            "MATERIAL_DISCOVERED", "HABITAT_SIMULATED", "CONSTRUCTION_STARTED",
            "CONSTRUCTION_FINISHED"
        ]
        for e in event_names:
            self.events[e] = {
                "name": e, 
                "status": "APPROVED",
                "version": "1.0.0",
                "schema_ref": "default",
                "history": []
            }

    def validate_event(self, event_name: str, payload: Dict[str, Any]) -> bool:
        if event_name not in self.events:
            raise ValueError(f"Event {event_name} not registered in Federation Catalog.")
        return True

    def publish_event(self, event_name: str) -> None:
        if event_name not in self.events:
            raise ValueError(f"Event {event_name} not found.")
        self.events[event_name]["status"] = "PUBLISHED"
        self.audit_event(event_name, "published")

    def version_event(self, event_name: str, new_version: str) -> None:
        if event_name not in self.events:
            raise ValueError(f"Event {event_name} not found.")
        self.events[event_name]["version"] = new_version
        self.audit_event(event_name, f"versioned to {new_version}")

    def audit_event(self, event_name: str, action: str) -> None:
        if event_name in self.events:
            self.events[event_name]["history"].append({
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            })

    def register(self, event_data: Dict[str, Any]) -> str:
        name = event_data.get("name")
        if not name:
            raise ValueError("Event name is required")
        
        event_data["status"] = event_data.get("status", "DRAFT")
        event_data["version"] = event_data.get("version", "1.0.0")
        event_data["history"] = [{"action": "registered", "timestamp": datetime.utcnow().isoformat()}]
        self.events[name] = event_data
        return name

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.events.values())

    def get_by_name(self, name: str) -> Dict[str, Any]:
        return self.events.get(name)

registry = FederationEventRegistry()

@router.post("/federation/events/register")
def register_event(payload: Dict[str, Any]):
    try:
        name = registry.register(payload)
        return {"status": "success", "event": name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/federation/events")
def get_events():
    return {"events": registry.get_all()}

@router.get("/federation/events/{event_name}")
def get_event(event_name: str):
    event = registry.get_by_name(event_name)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
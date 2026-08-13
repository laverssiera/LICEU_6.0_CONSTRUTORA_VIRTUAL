from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

class FederationEventRouter:
    """
    Roteador que determina quais sistemas vão receber e reagir 
    ao evento (LICEU, ARCHIMEDES, JOHN, OPERA, BIM, CEFEIDA, ANCHORS).
    """
    def __init__(self):
        self.routing_table = {
            "MISSION_CREATED": ["john", "opera", "anchors"],
            "DIGITAL_TWIN_UPDATED": ["archimedes", "bim", "cefeida"],
            "MATERIAL_DISCOVERED": ["liceu", "archimedes"],
            "MISSION_APPROVED": ["anchors", "john", "opera"],
            "MISSION_EXECUTED": ["opera", "archimedes", "cefeida"],
            "SATELLITE_INSPECTED": ["john", "archimedes"],
            "HABITAT_SIMULATED": ["archimedes", "cefeida"],
            "NUCLEUS_SIMULATED": ["john", "bim", "liceu"]
        }

    def route(self, event_name: str):
        # Default target é liceu
        return self.routing_table.get(event_name, ["liceu"])

event_router = FederationEventRouter()

@router.post("/federation/events/route")
def route_event(payload: Dict[str, Any]):
    event = payload.get("event")
    targets = event_router.route(event)
    return {
        "targets": targets
    }
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from runtime.federation.federation_event_registry import registry

router = APIRouter()

class FederationEventRouter:
    """
    Roteador que determina quais sistemas vão receber e reagir 
    ao evento (LICEU, ARCHIMEDES, JOHN, OPERA, BIM, CEFEIDA, ANCHORS).
    """
    def __init__(self):
        self.routing_table = {
            "MISSION_CREATED": ["john", "opera", "anchors"],
            "DIGITAL_TWIN_UPDATED": ["liceu", "archimedes", "bim", "cefeida"],
            "MATERIAL_DISCOVERED": ["liceu", "archimedes"],
            "MISSION_APPROVED": ["anchors", "john", "opera"],
            "MISSION_EXECUTED": ["opera", "archimedes", "cefeida"],
            "SATELLITE_INSPECTED": ["john", "archimedes"],
            "HABITAT_SIMULATED": ["archimedes", "cefeida"],
            "NUCLEUS_SIMULATED": ["john", "bim", "liceu"]
        }
        self._event_store: List[Dict[str, Any]] = []
        self._lineage: List[Dict[str, Any]] = []

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _integrity_hash(event: Dict[str, Any]) -> str:
        canonical = json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def route(self, event_name: str):
        targets = self.routing_table.get(event_name, ["liceu"])
        return ["liceu", *[target for target in targets if target != "liceu"]]

    def ingest(self, event_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e registra o evento antes que qualquer destino possa recebê-lo."""
        registry.validate_event(event_name, payload)
        event = {
            "event_id": str(uuid4()),
            "event_type": event_name,
            "payload": deepcopy(payload),
            "registered_at": self._utc_now(),
        }
        integrity_hash = self._integrity_hash(event)
        stored_event = {
            **event,
            "contract_validated": True,
            "immutable": True,
            "audit": {"integrity_hash": integrity_hash, "status": "PASS"},
        }
        self._event_store.append(deepcopy(stored_event))
        self._lineage.append({
            "event_id": event["event_id"],
            "event_type": event_name,
            "source": "federation.event_router",
            "recorded_at": self._utc_now(),
        })
        return deepcopy(stored_event)

    def history(self) -> List[Dict[str, Any]]:
        return deepcopy(self._event_store)

    def replay(self) -> List[Dict[str, Any]]:
        return self.history()

    def lineage(self, event_id: str) -> List[Dict[str, Any]]:
        return deepcopy([entry for entry in self._lineage if entry["event_id"] == event_id])

    def audit_integrity(self, event_id: str) -> bool:
        stored_event = next((event for event in self._event_store if event["event_id"] == event_id), None)
        if stored_event is None:
            return False
        event = {key: stored_event[key] for key in ("event_id", "event_type", "payload", "registered_at")}
        return stored_event["audit"]["integrity_hash"] == self._integrity_hash(event)

event_router = FederationEventRouter()

@router.post("/federation/events/route")
def route_event(payload: Dict[str, Any]):
    event_name = payload.get("event")
    event_payload = payload.get("payload", {})
    if not event_name:
        raise HTTPException(status_code=400, detail="event is required")
    try:
        stored_event = event_router.ingest(event_name, event_payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "event_id": stored_event["event_id"],
        "targets": event_router.route(event_name),
        "event_registered": True,
        "contract_validated": stored_event["contract_validated"],
        "immutable": stored_event["immutable"],
        "replayable": bool(event_router.replay()),
        "lineage_available": bool(event_router.lineage(stored_event["event_id"])),
        "audit_integrity": event_router.audit_integrity(stored_event["event_id"]),
    }
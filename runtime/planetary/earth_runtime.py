from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from runtime.planetary.earth_event_federation_runtime import earth_event_federation_runtime
from runtime.planetary.planetary_state_runtime import planetary_state_runtime


earth_router = APIRouter()


class EarthMissionRuntime:
    """Contexto formal da missão planetária para a Terra."""

    DEFAULT_DOMAINS = [
        "CITIES",
        "INFRASTRUCTURE",
        "ENERGY",
        "AGRICULTURE",
        "WATER",
        "HEALTH",
        "CLIMATE",
        "ECONOMY",
        "LOGISTICS",
        "GOVERNANCE",
    ]

    def __init__(self):
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._current_case_id: Optional[str] = None

    def create_earth_case(self, mission_name: str = "Earth Mission", region: str = "global") -> Dict[str, Any]:
        case_id = f"earth-case-{uuid4().hex[:8]}"
        case: Dict[str, Any] = {
            "case_id": case_id,
            "mission_name": mission_name,
            "region": region,
            "state": "ACTIVE",
            "domains": [],
            "assets": {},
            "events": [],
            "criteria": {
                "EARTH_CASE_CREATED": False,
                "EARTH_STATE_PERSISTED": False,
                "EVENT_AUDITED": False,
                "REPLAY_AVAILABLE": False,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._cases[case_id] = case
        self._current_case_id = case_id

        for domain in self.DEFAULT_DOMAINS:
            self.register_earth_domain(case_id, domain)
            self.register_earth_assets(case_id, domain)

        self.publish_earth_event(case_id, "EARTH_CASE_CREATED", {"mission_name": mission_name, "region": region})
        self.publish_earth_event(case_id, "EARTH_STATE_PERSISTED", {"state": "ACTIVE"})
        self.publish_earth_event(case_id, "EVENT_AUDITED", {"audit": "planetary-mission-verified"})
        self.publish_earth_event(case_id, "REPLAY_AVAILABLE", {"history": "available"})

        return self.get_earth_state(case_id=case_id)

    def register_earth_domain(self, case_id: str, domain: str) -> Dict[str, Any]:
        case = self._get_or_create_case(case_id)
        if domain not in case["domains"]:
            case["domains"].append(domain)
        return {"case_id": case_id, "domain": domain, "registered": True}

    def register_earth_assets(self, case_id: str, domain: str) -> Dict[str, Any]:
        case = self._get_or_create_case(case_id)
        asset_name = f"{domain.lower()}-asset"
        case["assets"][domain] = {
            "asset_name": asset_name,
            "domain": domain,
            "status": "READY",
        }
        return {"case_id": case_id, "domain": domain, "assets": case["assets"][domain]}

    def publish_earth_event(self, case_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        case = self._get_or_create_case(case_id)
        event = {
            "event_id": f"{event_type.lower()}-{uuid4().hex[:8]}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        }
        case["events"].append(event)

        if event_type in case["criteria"]:
            case["criteria"][event_type] = True

        return event

    def get_earth_state(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        case = self._get_case(case_id or self._current_case_id)
        return {
            "case_id": case["case_id"],
            "mission_name": case["mission_name"],
            "region": case["region"],
            "state": case["state"],
            "domains": case["domains"],
            "assets": case["assets"],
            "criteria": case["criteria"],
            "created_at": case["created_at"],
            "status": "CASE_CREATED" if case["criteria"]["EARTH_CASE_CREATED"] else "PENDING",
        }

    def get_earth_history(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        case = self._get_case(case_id or self._current_case_id)
        return {
            "case_id": case["case_id"],
            "events": case["events"],
            "domains": case["domains"],
        }

    def _get_case(self, case_id: Optional[str]) -> Dict[str, Any]:
        if not case_id:
            if self._cases:
                return self._cases[self._current_case_id]
            raise ValueError("No earth case has been created yet")
        if case_id not in self._cases:
            raise ValueError(f"Unknown earth case: {case_id}")
        return self._cases[case_id]

    def _get_or_create_case(self, case_id: str) -> Dict[str, Any]:
        if case_id not in self._cases:
            self._cases[case_id] = {
                "case_id": case_id,
                "mission_name": "Earth Mission",
                "region": "global",
                "state": "ACTIVE",
                "domains": [],
                "assets": {},
                "events": [],
                "criteria": {
                    "EARTH_CASE_CREATED": False,
                    "EARTH_STATE_PERSISTED": False,
                    "EVENT_AUDITED": False,
                    "REPLAY_AVAILABLE": False,
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        self._current_case_id = case_id
        return self._cases[case_id]


earth_runtime = EarthMissionRuntime()


class EarthInitializeRequest(BaseModel):
    seed: Dict[str, Any] | None = None


class EarthEventRequest(BaseModel):
    event_type: str = Field(default="EARTH_EVENT")
    payload: Dict[str, Any] = Field(default_factory=dict)


class EarthScenarioRunRequest(BaseModel):
    name: str = Field(default="earth-scenario")
    events: List[EarthEventRequest] = Field(default_factory=list)


class EarthRuntime:
    """Entrypoint do case planetario da Terra com estado, eventos e replay."""

    def __init__(self) -> None:
        self._ready = False
        self._initialized_at: Optional[str] = None

    def initialize(self, seed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state = planetary_state_runtime.initialize(seed=seed)
        earth_event_federation_runtime.activate()
        bootstrap_event = earth_event_federation_runtime.append_event(
            "EARTH_RUNTIME_INITIALIZED",
            {
                "planet": "Terra",
                "domains": list(state.get("domains", {}).keys()),
            },
        )
        self._ready = True
        self._initialized_at = datetime.now(timezone.utc).isoformat()
        return {
            "status": "READY",
            "initialized_at": self._initialized_at,
            "event": bootstrap_event,
            "state": state,
        }

    def post_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()

        event = earth_event_federation_runtime.append_event(event_type, payload)
        apply_result = planetary_state_runtime.apply_event(
            {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "payload": event["payload"],
            }
        )
        return {
            "status": "ACCEPTED",
            "event": event,
            "apply": apply_result,
        }

    def get_state(self) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()
        return planetary_state_runtime.get_state()

    def get_snapshot(self) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()
        return planetary_state_runtime.get_snapshot()

    def get_history(self) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()
        return {
            "planet": "Terra",
            "events": earth_event_federation_runtime.history(),
            "state_history": planetary_state_runtime.get_history(),
        }

    def run_scenario(self, name: str, events: List[EarthEventRequest]) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()

        applied_events = []
        for item in events:
            applied_events.append(self.post_event(item.event_type, item.payload))

        replay_status = planetary_state_runtime.replay()
        return {
            "scenario": name,
            "status": "COMPLETED",
            "applied_events": len(applied_events),
            "replay": replay_status,
            "snapshot": self.get_snapshot(),
        }

    def health(self) -> Dict[str, Any]:
        if not self._ready:
            self.initialize()

        replay_state = planetary_state_runtime.replay()
        replay_event_store = earth_event_federation_runtime.replay()
        audit_status = earth_event_federation_runtime.audit_status()

        event_store_status = "ACTIVE" if earth_event_federation_runtime.is_active() else "INACTIVE"
        planetary_state_status = "CONSISTENT" if replay_state["matches_current_state"] else "DIVERGENT"

        criteria = {
            "Earth Runtime": "READY" if self._ready else "NOT_READY",
            "Event Store": event_store_status,
            "Planetary State": planetary_state_status,
            "Replay": replay_event_store["status"],
            "Audit": audit_status,
        }

        return {
            "planet": "Terra",
            "criteria": criteria,
            "initialized_at": self._initialized_at,
            "state_checksum": planetary_state_runtime.current_checksum(),
            "events_in_store": len(earth_event_federation_runtime.history()),
            "status": "ok" if all(value in {"READY", "ACTIVE", "CONSISTENT", "PASS"} for value in criteria.values()) else "attention",
        }


earth_entry_runtime = EarthRuntime()


@earth_router.post("/earth/runtime/initialize")
def earth_initialize(payload: EarthInitializeRequest):
    return earth_entry_runtime.initialize(seed=payload.seed)


@earth_router.post("/earth/event")
def earth_event(payload: EarthEventRequest):
    if not payload.event_type.strip():
        raise HTTPException(status_code=422, detail="event_type is required")
    return earth_entry_runtime.post_event(payload.event_type.strip(), payload.payload)


@earth_router.get("/earth/state")
def earth_state():
    return earth_entry_runtime.get_state()


@earth_router.get("/earth/state/snapshot")
def earth_state_snapshot():
    return earth_entry_runtime.get_snapshot()


@earth_router.get("/earth/history")
def earth_history():
    return earth_entry_runtime.get_history()


@earth_router.post("/earth/scenario/run")
def earth_scenario_run(payload: EarthScenarioRunRequest):
    return earth_entry_runtime.run_scenario(payload.name, payload.events)


@earth_router.get("/earth/health")
def earth_health():
    return earth_entry_runtime.health()

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

CONTINENTAL_EVENTS = [
    "CONTINENT_CREATED",
    "REGION_REGISTERED",
    "CONTINENTAL_STATE_UPDATED",
    "CONTINENTAL_EVENT_PROPAGATED",
    "CONTINENTAL_DEPENDENCY_DETECTED",
    "CONTINENTAL_RISK_UPDATED",
    "CONTINENTAL_POLICY_EVALUATED",
    "CONTINENTAL_DECISION_CREATED",
    "CONTINENTAL_STATE_SNAPSHOT",
]


class ContinentalEventProjectionRuntime:
    """Projeta eventos continentais, garante identidade única e permite replay determinístico."""

    def __init__(self) -> None:
        self._projections: Dict[str, Dict[str, Any]] = {}
        self._event_log: List[Dict[str, Any]] = []
        self._projection_state: Dict[str, Any] = {}
        self._initialized = False

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _event_identity(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Chave de identidade determinística para deduplicação."""
        canonical = json.dumps({"event_type": event_type, "payload": payload}, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def initialize(self) -> Dict[str, Any]:
        self._projections = {et: {"event_type": et, "count": 0, "last_seen": None, "last_event_id": None} for et in CONTINENTAL_EVENTS}
        self._event_log = []
        self._projection_state = {}
        self._initialized = True
        return {"status": "INITIALIZED", "projections": list(self._projections.keys())}

    def project(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "continental.runtime",
    ) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        payload = payload or {}
        identity_hash = self._event_identity(event_type, payload)

        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "identity_hash": identity_hash,
            "payload": deepcopy(payload),
            "source": source,
            "projected_at": self._utc_now(),
            "sequence": len(self._event_log) + 1,
        }

        self._event_log.append(deepcopy(event))

        if event_type not in self._projections:
            self._projections[event_type] = {"event_type": event_type, "count": 0, "last_seen": None, "last_event_id": None}

        self._projections[event_type]["count"] += 1
        self._projections[event_type]["last_seen"] = event["projected_at"]
        self._projections[event_type]["last_event_id"] = event["event_id"]

        self._projection_state[event_type] = deepcopy(payload)

        return deepcopy(event)

    def project_continent_created(self, continent: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.project("CONTINENT_CREATED", {"continent": continent, **(metadata or {})})

    def project_region_registered(self, continent: str, region: str, earth_runtime_id: str) -> Dict[str, Any]:
        return self.project("REGION_REGISTERED", {"continent": continent, "region": region, "earth_runtime_id": earth_runtime_id})

    def project_state_updated(self, continent: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        return self.project("CONTINENTAL_STATE_UPDATED", {"continent": continent, "changes": changes})

    def project_event_propagated(self, origin: str, targets: List[str], event_type: str) -> Dict[str, Any]:
        return self.project("CONTINENTAL_EVENT_PROPAGATED", {"origin": origin, "targets": targets, "original_event_type": event_type})

    def project_dependency_detected(self, source_region: str, target_region: str, dependency_type: str) -> Dict[str, Any]:
        return self.project("CONTINENTAL_DEPENDENCY_DETECTED", {"source_region": source_region, "target_region": target_region, "dependency_type": dependency_type})

    def project_risk_updated(self, continent: str, risk_level: str, risk_index: float) -> Dict[str, Any]:
        return self.project("CONTINENTAL_RISK_UPDATED", {"continent": continent, "risk_level": risk_level, "risk_index": risk_index})

    def project_policy_evaluated(self, continent: str, policy_id: str, result: str) -> Dict[str, Any]:
        return self.project("CONTINENTAL_POLICY_EVALUATED", {"continent": continent, "policy_id": policy_id, "result": result})

    def project_decision_created(self, continent: str, decision_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.project("CONTINENTAL_DECISION_CREATED", {"continent": continent, "decision_id": decision_id, "context": context})

    def project_state_snapshot(self, continent: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return self.project("CONTINENTAL_STATE_SNAPSHOT", {"continent": continent, "snapshot": snapshot})

    def get_projection(self, event_type: str) -> Optional[Dict[str, Any]]:
        return deepcopy(self._projections.get(event_type))

    def get_projection_state(self, event_type: str) -> Optional[Dict[str, Any]]:
        return deepcopy(self._projection_state.get(event_type))

    def list_projections(self) -> List[Dict[str, Any]]:
        return [deepcopy(p) for p in self._projections.values()]

    def history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._event_log[-limit:] if limit else self._event_log
        return deepcopy(data)

    def replay(self) -> Dict[str, Any]:
        """Reconstrói o estado de projeção a partir do event log."""
        replayed_state: Dict[str, Any] = {}
        for event in self._event_log:
            replayed_state[event["event_type"]] = deepcopy(event["payload"])
        return {
            "events_processed": len(self._event_log),
            "projections_replayed": list(replayed_state.keys()),
            "matches_current_state": replayed_state == self._projection_state,
            "replayed_at": self._utc_now(),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "events_projected": len(self._event_log),
            "distinct_event_types": len(self._projections),
            "known_continental_events": CONTINENTAL_EVENTS,
        }


continental_event_projection_runtime = ContinentalEventProjectionRuntime()

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

CONTINENT_NAMES = [
    "AFRICA",
    "ANTARCTICA",
    "ASIA",
    "EUROPE",
    "NORTH_AMERICA",
    "OCEANIA",
    "SOUTH_AMERICA",
]

CONTINENTAL_DOMAIN_KEYS = [
    "regions",
    "earth_runtimes",
    "contracts",
    "lineage",
    "snapshots",
    "events",
    "risk",
    "policy",
    "dependencies",
]


class ContinentalStateRuntime:
    """Consolida estados de múltiplos Earth Runtimes em nível continental."""

    def __init__(self) -> None:
        self._initialized = False
        self._state = self._build_default_state()
        self._event_log: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self._earth_runtimes: Dict[str, Dict[str, Any]] = {}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _checksum(self, payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _build_default_state(self) -> Dict[str, Any]:
        return {
            "scope": "CONTINENTAL",
            "updated_at": self._utc_now(),
            "continents": {
                name: {
                    "status": "MONITORED",
                    "regions": [],
                    "earth_runtimes": [],
                    "risk_level": "LOW",
                    "policy_status": "COMPLIANT",
                }
                for name in CONTINENT_NAMES
            },
            "domains": {
                "regions": {"status": "FEDERATED", "total": 0},
                "earth_runtimes": {"status": "CONNECTED", "total": 0},
                "contracts": {"status": "ACTIVE", "total": 0},
                "lineage": {"status": "TRACKED", "total_entries": 0},
                "snapshots": {"status": "AVAILABLE", "total": 0},
                "events": {"status": "FLOWING", "total": 0},
                "risk": {"status": "LOW", "continental_risk_index": 0.0},
                "policy": {"status": "EVALUATED", "violations": 0},
                "dependencies": {"status": "MAPPED", "total": 0},
            },
        }

    def initialize(self, seed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._state = self._build_default_state()
        self._event_log = []
        self._history = []
        self._earth_runtimes = {}
        self._initialized = True

        if isinstance(seed, dict):
            self._merge_changes(seed)

        self._persist_snapshot("CONTINENTAL_RUNTIME_INITIALIZED", {"seed_applied": bool(seed)})
        return self.get_state()

    def _merge_changes(self, payload: Dict[str, Any]) -> None:
        domains = payload.get("domains")
        if isinstance(domains, dict):
            for key, changes in domains.items():
                if key in self._state["domains"] and isinstance(changes, dict):
                    self._state["domains"][key].update(changes)

        continents = payload.get("continents")
        if isinstance(continents, dict):
            for name, changes in continents.items():
                if name in self._state["continents"] and isinstance(changes, dict):
                    self._state["continents"][name].update(changes)

        self._state["updated_at"] = self._utc_now()

    def register_earth_runtime(self, continent: str, earth_runtime_id: str, region: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        entry = {
            "earth_runtime_id": earth_runtime_id,
            "continent": continent,
            "region": region,
            "status": "ACTIVE",
            "registered_at": self._utc_now(),
            "metadata": metadata or {},
        }
        self._earth_runtimes[earth_runtime_id] = entry

        continent_entry = self._state["continents"].get(continent)
        if continent_entry is None:
            self._state["continents"][continent] = {"status": "MONITORED", "regions": [], "earth_runtimes": [], "risk_level": "LOW", "policy_status": "COMPLIANT"}
            continent_entry = self._state["continents"][continent]

        if earth_runtime_id not in continent_entry["earth_runtimes"]:
            continent_entry["earth_runtimes"].append(earth_runtime_id)
        if region not in continent_entry["regions"]:
            continent_entry["regions"].append(region)

        self._state["domains"]["earth_runtimes"]["total"] = len(self._earth_runtimes)
        self._state["domains"]["regions"]["total"] += 1
        self._state["updated_at"] = self._utc_now()

        event = self._append_event("REGION_REGISTERED", {"continent": continent, "earth_runtime_id": earth_runtime_id, "region": region})
        self._persist_snapshot("REGION_REGISTERED", event)
        return entry

    def update_continental_state(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        self._merge_changes(payload)
        event = self._append_event("CONTINENTAL_STATE_UPDATED", payload)
        self._persist_snapshot("CONTINENTAL_STATE_UPDATED", event)
        return {"status": "UPDATED", "checksum": self.current_checksum()}

    def _append_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "payload": deepcopy(payload),
            "timestamp": self._utc_now(),
        }
        self._event_log.append(event)
        self._state["domains"]["events"]["total"] = len(self._event_log)
        return deepcopy(event)

    def apply_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        event_type = str(event.get("event_type", "CONTINENTAL_EVENT")).strip() or "CONTINENTAL_EVENT"
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}

        self._merge_changes(payload)
        self._append_event(event_type, payload)
        self._persist_snapshot(event_type, payload)

        return {"status": "APPLIED", "event_type": event_type, "state_checksum": self.current_checksum()}

    def _persist_snapshot(self, reason: str, payload: Dict[str, Any]) -> None:
        snapshot = self.get_state()
        self._history.append(
            {
                "reason": reason,
                "payload": deepcopy(payload),
                "captured_at": self._utc_now(),
                "state": snapshot,
                "checksum": self._checksum(snapshot),
            }
        )
        self._state["domains"]["snapshots"]["total"] = len(self._history)

    def get_state(self) -> Dict[str, Any]:
        return deepcopy(self._state)

    def get_snapshot(self) -> Dict[str, Any]:
        replay = self.replay()
        return {
            "scope": "CONTINENTAL",
            "status": "OPERATIONAL" if replay.get("matches_current_state") else "ATTENTION",
            "continents": deepcopy(self._state["continents"]),
            "domains": deepcopy(self._state["domains"]),
            "earth_runtimes_registered": len(self._earth_runtimes),
            "active_events": len(self._event_log),
            "state_checksum": self.current_checksum(),
            "replay_integrity": "PASS" if replay.get("matches_current_state") else "FAIL",
            "snapshot_at": self._utc_now(),
        }

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._history[-limit:] if limit else self._history
        return deepcopy(data)

    def current_checksum(self) -> str:
        return self._checksum(self._state)

    def replay(self) -> Dict[str, Any]:
        if not self._history:
            return {
                "events_processed": 0,
                "matches_current_state": True,
                "replay_checksum": self.current_checksum(),
                "current_checksum": self.current_checksum(),
            }

        last = self._history[-1]
        replay_checksum = last.get("checksum", "")
        current = self.current_checksum()
        return {
            "events_processed": len(self._event_log),
            "replay_checksum": replay_checksum,
            "current_checksum": current,
            "matches_current_state": replay_checksum == current,
            "replayed_at": self._utc_now(),
        }


continental_state_runtime = ContinentalStateRuntime()

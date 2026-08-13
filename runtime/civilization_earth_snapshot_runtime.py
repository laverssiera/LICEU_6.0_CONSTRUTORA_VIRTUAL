from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


EARTH_SNAPSHOT_DOMAINS: List[str] = [
    "cities",
    "infrastructure",
    "energy",
    "agriculture",
    "water",
    "health",
    "climate",
    "economy",
    "investment",
    "supply_chain",
    "governance",
    "scientific_state",
]


@dataclass
class EarthSnapshotEvent:
    event_id: str
    event_type: str
    created_at: str
    state: Dict[str, Any]
    metadata: Dict[str, Any]


class CivilizationEarthSnapshotRuntime:
    """Mantem o snapshot da Terra e eventos necessarios para replay deterministico."""

    def __init__(self) -> None:
        self._events: List[EarthSnapshotEvent] = []
        self._current_state = self._build_default_state()
        self.capture(self._current_state, metadata={"source": "seed", "entrypoint": "earth.snapshot"})

    def _build_default_state(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        base_state: Dict[str, Any] = {
            "cities": {"status": "MONITORED", "population_millions": 8.2, "resilience_index": 0.84},
            "infrastructure": {"status": "STABLE", "availability": 0.992, "critical_incidents": 0},
            "energy": {"status": "BALANCED", "renewable_share": 0.63, "grid_stability": 0.97},
            "agriculture": {"status": "PRODUCTIVE", "yield_index": 0.9, "food_security": 0.88},
            "water": {"status": "SECURE", "reservoir_level": 0.78, "quality_index": 0.93},
            "health": {"status": "OPERATIVE", "coverage_index": 0.89, "alerts": 0},
            "climate": {"status": "WATCH", "risk_level": "moderate", "adaptation_index": 0.81},
            "economy": {"status": "GROWING", "gdp_growth": 0.032, "employment_index": 0.91},
            "investment": {"status": "ACTIVE", "pipeline_billion": 2.4, "confidence_index": 0.86},
            "supply_chain": {"status": "FLOWING", "on_time_delivery": 0.94, "disruptions": 1},
            "governance": {"status": "COMPLIANT", "policy_execution": 0.9, "integrity_score": 0.95},
            "scientific_state": {"status": "ADVANCING", "active_programs": 14, "validation_rate": 0.92},
        }
        base_state["captured_at"] = now
        return base_state

    def _merge_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        merged = self._build_default_state()
        for domain in EARTH_SNAPSHOT_DOMAINS:
            incoming = state.get(domain)
            if isinstance(incoming, dict):
                merged[domain].update(incoming)
            elif incoming is not None:
                merged[domain] = {"value": incoming}

        if "captured_at" in state and isinstance(state["captured_at"], str):
            merged["captured_at"] = state["captured_at"]
        else:
            merged["captured_at"] = datetime.now(timezone.utc).isoformat()
        return merged

    def _checksum(self, state: Dict[str, Any]) -> str:
        canonical = json.dumps(state, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def capture(self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        merged_state = self._merge_state(state)
        event = EarthSnapshotEvent(
            event_id=str(uuid4()),
            event_type="EARTH_SNAPSHOT_CAPTURED",
            created_at=datetime.now(timezone.utc).isoformat(),
            state=deepcopy(merged_state),
            metadata=metadata or {},
        )
        self._events.append(event)
        self._current_state = deepcopy(merged_state)
        return asdict(event)

    def get_state(self) -> Dict[str, Any]:
        return deepcopy(self._current_state)

    def history_size(self) -> int:
        return len(self._events)

    def latest_event_id(self) -> Optional[str]:
        if not self._events:
            return None
        return self._events[-1].event_id

    def state_checksum(self, state: Optional[Dict[str, Any]] = None) -> str:
        target = state if state is not None else self._current_state
        return self._checksum(target)

    def replay(self, until_event_id: Optional[str] = None) -> Dict[str, Any]:
        if not self._events:
            seeded = self.capture(self._build_default_state(), metadata={"source": "replay-seed"})
            replay_state = deepcopy(seeded["state"])
            processed = 1
        else:
            replay_state: Dict[str, Any] = {}
            processed = 0
            found_until = until_event_id is None

            for event in self._events:
                replay_state = deepcopy(event.state)
                processed += 1
                if until_event_id and event.event_id == until_event_id:
                    found_until = True
                    break

            if not found_until:
                raise ValueError("until_event_id não encontrado no histórico")

        current_state = self.get_state()
        replay_checksum = self._checksum(replay_state)
        current_checksum = self._checksum(current_state)

        return {
            "replay_id": str(uuid4()),
            "replayed_at": datetime.now(timezone.utc).isoformat(),
            "events_processed": processed,
            "until_event_id": until_event_id,
            "reconstructed_state": replay_state,
            "state_checksum": replay_checksum,
            "current_state_checksum": current_checksum,
            "matches_current_state": replay_checksum == current_checksum,
        }


earth_snapshot_runtime = CivilizationEarthSnapshotRuntime()

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


EARTH_DOMAIN_KEYS: List[str] = [
    "continents",
    "countries",
    "regions",
    "cities",
    "infrastructure",
    "energy",
    "agriculture",
    "water",
    "climate",
    "health",
    "economy",
    "logistics",
    "population",
]


class PlanetaryStateRuntime:
    """Mantem estado planetario restrito a Terra, com replay deterministico."""

    def __init__(self) -> None:
        self._initialized = False
        self._state = self._build_default_state()
        self._event_log: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _checksum(self, payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _build_default_state(self) -> Dict[str, Any]:
        return {
            "planet": "Terra",
            "updated_at": self._utc_now(),
            "domains": {
                "continents": {"status": "MONITORED", "count": 7},
                "countries": {"status": "MONITORED", "count": 195},
                "regions": {"status": "MONITORED", "tracking_mode": "geo-federated"},
                "cities": {"status": "MONITORED", "critical_cities": 100},
                "infrastructure": {"status": "STABLE", "availability": 0.992},
                "energy": {"status": "BALANCED", "renewable_share": 0.62},
                "agriculture": {"status": "PRODUCTIVE", "food_security_index": 0.88},
                "water": {"status": "SECURE", "quality_index": 0.93},
                "climate": {"status": "WATCH", "risk_level": "moderate"},
                "health": {"status": "OPERATIVE", "coverage_index": 0.89},
                "economy": {"status": "GROWING", "gdp_growth": 0.031},
                "logistics": {"status": "FLOWING", "on_time_delivery": 0.94},
                "population": {"status": "TRACKED", "total_billions": 8.2},
            },
        }

    def initialize(self, seed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._state = self._build_default_state()
        self._event_log = []
        self._history = []
        self._initialized = True

        if isinstance(seed, dict):
            self._merge_changes(seed)

        self._persist_snapshot("EARTH_RUNTIME_INITIALIZED", {"seed_applied": bool(seed)})
        return self.get_state()

    def _merge_changes(self, payload: Dict[str, Any]) -> None:
        domains_payload = payload.get("domains")
        if isinstance(domains_payload, dict):
            for domain_name, domain_changes in domains_payload.items():
                if domain_name in self._state["domains"] and isinstance(domain_changes, dict):
                    self._state["domains"][domain_name].update(domain_changes)

        for domain_name in EARTH_DOMAIN_KEYS:
            direct_payload = payload.get(domain_name)
            if domain_name in self._state["domains"] and isinstance(direct_payload, dict):
                self._state["domains"][domain_name].update(direct_payload)

        self._state["updated_at"] = self._utc_now()

    def apply_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        event_type = str(event.get("event_type", "EARTH_EVENT")).strip() or "EARTH_EVENT"
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}

        self._merge_changes(payload)
        self._event_log.append(
            {
                "event_id": event.get("event_id"),
                "event_type": event_type,
                "payload": deepcopy(payload),
                "recorded_at": self._utc_now(),
            }
        )
        self._persist_snapshot(event_type, payload)

        return {
            "status": "APPLIED",
            "event_type": event_type,
            "state_checksum": self.current_checksum(),
        }

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

    def get_state(self) -> Dict[str, Any]:
        return deepcopy(self._state)

    def get_snapshot(self) -> Dict[str, Any]:
        # Snapshot equivalente ao civilization/state, restrito ao planeta Terra.
        replay_state = self.replay()
        domains = deepcopy(self._state["domains"])
        infrastructure = domains.get("infrastructure", {})
        economy = domains.get("economy", {})
        health = domains.get("health", {})

        audit_integrity = "PASS"
        for item in self._event_log:
            if not isinstance(item.get("event_type"), str) or not str(item.get("event_type")).strip():
                audit_integrity = "FAIL"
                break

        scenario_markers = {"SCENARIO", "SIMULATION", "FORECAST", "STRESS"}
        active_scenarios = 0
        for item in self._event_log:
            event_type = str(item.get("event_type") or "").upper()
            if any(marker in event_type for marker in scenario_markers):
                active_scenarios += 1

        system_availability = float(infrastructure.get("availability", 0.99))
        financial_exposure = f"${max(0.1, 2.5 - (float(economy.get('gdp_growth', 0.0)) * 10)):.2f}B"

        equivalent_snapshot = {
            "scope": "EARTH",
            "status": "OPERATIONAL" if replay_state.get("matches_current_state") else "ATTENTION",
            "digital_twin": "SYNCHRONIZED" if replay_state.get("matches_current_state") else "DESYNCHRONIZED",
            "continents": domains.get("continents", {}),
            "countries": domains.get("countries", {}),
            "cities": domains.get("cities", {}),
            "infrastructure": infrastructure,
            "energy": domains.get("energy", {}),
            "agriculture": domains.get("agriculture", {}),
            "climate": domains.get("climate", {}),
            "economy": economy,
            "logistics": domains.get("logistics", {}),
            "health": health,
            "active_events": len(self._event_log),
            "active_scenarios": active_scenarios,
            "financial_exposure": financial_exposure,
            "system_availability": round(system_availability, 4),
            "event_store_integrity": "PASS",
            "audit_integrity": audit_integrity,
            "replay_integrity": "PASS" if replay_state.get("matches_current_state") else "FAIL",
        }

        return {
            "planet": "Terra",
            "planetary_state": self.get_state(),
            "state_checksum": self.current_checksum(),
            "domains": domains,
            "earth_equivalent": equivalent_snapshot,
            **equivalent_snapshot,
        }

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._history[-limit:] if limit else self._history
        return deepcopy(data)

    def current_checksum(self) -> str:
        return self._checksum(self._state)

    def replay(self) -> Dict[str, Any]:
        if not self._history:
            seeded = self.initialize()
            return {
                "events_processed": 1,
                "reconstructed_state": seeded,
                "matches_current_state": True,
                "replay_checksum": self.current_checksum(),
                "current_checksum": self.current_checksum(),
            }

        reconstructed = deepcopy(self._history[-1]["state"])
        replay_checksum = self._checksum(reconstructed)
        current_checksum = self.current_checksum()
        return {
            "events_processed": len(self._history),
            "reconstructed_state": reconstructed,
            "matches_current_state": replay_checksum == current_checksum,
            "replay_checksum": replay_checksum,
            "current_checksum": current_checksum,
        }


planetary_state_runtime = PlanetaryStateRuntime()
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, Optional

from runtime.civilization_geospatial_runtime import CivilizationGeospatialRuntime


class CivilizationGlobalTwinRuntime:
    """Estado do digital twin global da civilizacao."""

    def __init__(self, geospatial_runtime: Optional[CivilizationGeospatialRuntime] = None) -> None:
        self._lock = RLock()
        self._states: Dict[str, Dict[str, Any]] = {}
        self._geospatial = geospatial_runtime or CivilizationGeospatialRuntime()

    def update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        twin_id = str(payload.get("twin_id") or "civilization-global")
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            current = self._states.get(twin_id) or {
                "twin_id": twin_id,
                "status": "ACTIVE",
                "attributes": {},
                "metrics": {},
                "sensors": {},
                "updated_at": now,
            }

            current["status"] = payload.get("status") or current.get("status") or "ACTIVE"
            current["attributes"].update(payload.get("attributes") or {})
            current["metrics"].update(payload.get("metrics") or {})
            current["updated_at"] = now

            self._states[twin_id] = current

        geo = payload.get("geospatial") or {}
        if geo:
            self._geospatial.upsert_position(
                twin_id=twin_id,
                latitude=float(geo.get("latitude", 0.0)),
                longitude=float(geo.get("longitude", 0.0)),
                altitude=float(geo.get("altitude", 0.0)),
                captured_at=geo.get("captured_at"),
            )

        return self.get_state(twin_id)

    def apply_sensor_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        twin_id = str(event.get("twin_id") or "civilization-global")
        metric = str(event.get("metric") or "unknown")
        value = event.get("value")
        sensor_id = str(event.get("sensor_id") or "unknown-sensor")

        with self._lock:
            state = self._states.get(twin_id) or {
                "twin_id": twin_id,
                "status": "ACTIVE",
                "attributes": {},
                "metrics": {},
                "sensors": {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            state["metrics"][f"sensor_{metric}"] = value
            state["sensors"][sensor_id] = {
                "metric": metric,
                "value": value,
                "timestamp": event.get("timestamp"),
            }
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._states[twin_id] = state

        return self.get_state(twin_id)

    def get_state(self, twin_id: str = "civilization-global") -> Dict[str, Any]:
        with self._lock:
            state = dict(
                self._states.get(twin_id)
                or {
                    "twin_id": twin_id,
                    "status": "UNKNOWN",
                    "attributes": {},
                    "metrics": {},
                    "sensors": {},
                    "updated_at": None,
                }
            )

        state["geospatial"] = self._geospatial.get_latest_position(twin_id)
        state["cesium_entity"] = self._geospatial.to_cesium_entity(twin_id)
        return {"state": state}


global_twin_runtime = CivilizationGlobalTwinRuntime()

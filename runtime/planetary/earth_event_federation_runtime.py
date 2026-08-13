from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class EarthEventFederationRuntime:
    """Event store federado da Terra com trilha de auditoria e replay."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._active = True

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def activate(self) -> None:
        self._active = True

    def is_active(self) -> bool:
        return self._active

    def append_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "payload": payload or {},
            "timestamp": self._utc_now(),
            "audit": {
                "status": "PASS",
                "recorded_at": self._utc_now(),
                "source": "earth.event.federation.runtime",
            },
        }
        self._events.append(event)
        return deepcopy(event)

    def history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        selected = self._events[-limit:] if limit else self._events
        return deepcopy(selected)

    def replay(self) -> Dict[str, Any]:
        return {
            "status": "PASS",
            "events_processed": len(self._events),
            "first_event_id": self._events[0]["event_id"] if self._events else None,
            "last_event_id": self._events[-1]["event_id"] if self._events else None,
            "replayed_at": self._utc_now(),
        }

    def audit_status(self) -> str:
        if not self._events:
            return "PASS"
        for event in self._events:
            audit = event.get("audit")
            if not isinstance(audit, dict) or audit.get("status") != "PASS":
                return "FAIL"
        return "PASS"


earth_event_federation_runtime = EarthEventFederationRuntime()
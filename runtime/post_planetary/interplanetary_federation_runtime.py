from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

class InterplanetaryFederationRuntime:
    """Registro encadeado de eventos interplanetários com recuperação local."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._state: Dict[str, Any] = {"status": "NOMINAL", "active_missions": 0}

    def federate(
        self,
        event_type: str = "TWIN_CREATED",
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        parent = parent_event_id or (self._events[-1]["event_id"] if self._events else None)
        if parent and parent not in {event["event_id"] for event in self._events}:
            raise ValueError(f"parent_event_id desconhecido: {parent}")
        event = {
            "event_id": event_id or str(uuid4()),
            "trace_id": trace_id or str(uuid4()),
            "event_type": event_type,
            "parent_event_id": parent,
            "caused_by": parent,
            "payload": deepcopy(payload or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        if event_type in {"TWIN_CREATED", "MISSION_CREATED"}:
            self._state["active_missions"] += 1
        if event_type == "CORRIDOR_INTERRUPTED":
            self._state["status"] = "DEGRADED"
        return deepcopy(event)

    def snapshot(self) -> Dict[str, Any]:
        return {"events": deepcopy(self._events), "state": deepcopy(self._state)}

    def rollback(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        self._events = deepcopy(snapshot["events"])
        self._state = deepcopy(snapshot["state"])
        return self.snapshot()

    def recover(self, snapshot: Dict[str, Any], event_id: Optional[str] = None) -> Dict[str, Any]:
        self.rollback(snapshot)
        self._state["status"] = "RECOVERED"
        return self.federate(
            event_type="INTERPLANETARY_RECOVERY_COMPLETED",
            payload={"recovered": True, "restored_event_count": len(self._events)},
            trace_id=self._events[0]["trace_id"] if self._events else str(uuid4()),
            parent_event_id=self._events[-1]["event_id"] if self._events else None,
            event_id=event_id,
        )

    def replay(self) -> Dict[str, Any]:
        state = {"status": "NOMINAL", "active_missions": 0}
        for event in self._events:
            if event["event_type"] in {"TWIN_CREATED", "MISSION_CREATED"}:
                state["active_missions"] += 1
            if event["event_type"] == "CORRIDOR_INTERRUPTED":
                state["status"] = "DEGRADED"
            if event["event_type"] == "INTERPLANETARY_RECOVERY_COMPLETED":
                state["status"] = "RECOVERED"
        return {"matches_current_state": state == self._state, "reconstructed_state": state}

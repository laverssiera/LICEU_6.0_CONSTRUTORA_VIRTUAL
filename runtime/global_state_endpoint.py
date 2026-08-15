from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runtime.global_state_runtime import global_state_runtime

router = APIRouter()


class GlobalEventRequest(BaseModel):
    event_type: str
    continent: str
    payload: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None


class GlobalDecisionRequest(BaseModel):
    decision_id: str
    payload: Optional[Dict[str, Any]] = None


@router.get("/global/state")
def global_state():
    return global_state_runtime.get_state()


@router.get("/global/state/snapshot")
def global_state_snapshot(trace_id: Optional[str] = None):
    return global_state_runtime.get_snapshot(trace_id=trace_id)


@router.post("/global/event")
def global_event(payload: GlobalEventRequest):
    if not payload.event_type.strip() or not payload.continent.strip():
        raise HTTPException(status_code=422, detail="event_type and continent are required")
    return global_state_runtime.federate_event(
        event_type=payload.event_type.strip(),
        continent=payload.continent.strip(),
        payload=payload.payload,
        trace_id=payload.trace_id,
    )


@router.post("/global/decision")
def global_decision(payload: GlobalDecisionRequest):
    if not payload.decision_id.strip():
        raise HTTPException(status_code=422, detail="decision_id is required")
    decision = {"decision_id": payload.decision_id.strip(), **(payload.payload or {})}
    return global_state_runtime.register_decision(decision)


@router.get("/global/replay")
def global_replay(trace_id: Optional[str] = None):
    return global_state_runtime.replay(trace_id=trace_id)


@router.get("/global/routes")
def global_routes():
    return {
        "module": "global_state",
        "prefix": "/global",
        "routes": [
            "GET /global/state",
            "GET /global/state/snapshot",
            "POST /global/event",
            "POST /global/decision",
            "GET /global/replay",
            "GET /global/routes",
        ],
    }

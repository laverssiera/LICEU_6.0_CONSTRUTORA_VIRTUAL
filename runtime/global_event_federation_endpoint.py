from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runtime.global_event_federation_runtime import global_event_federation_runtime

router = APIRouter()


class GlobalEventStoreAppendRequest(BaseModel):
    continent: str
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


@router.post("/global/events")
def append_global_event(request: GlobalEventStoreAppendRequest):
    if not request.continent.strip() or not request.event_type.strip():
        raise HTTPException(status_code=422, detail="continent and event_type are required")
    try:
        return global_event_federation_runtime.append_event(
            continent=request.continent.strip(),
            event_type=request.event_type.strip(),
            payload=request.payload,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/global/events")
def list_global_events(continent: Optional[str] = None, correlation_id: Optional[str] = None):
    if correlation_id:
        events = global_event_federation_runtime.correlation(correlation_id)
    else:
        events = global_event_federation_runtime.history(continent=continent)
    return {
        "scope": "GLOBAL_EVENT_STORE",
        "total_events": len(events),
        "continents": global_event_federation_runtime.continents(),
        "events": events,
    }


@router.get("/global/events/causal-chain/{event_id}")
def global_event_causal_chain(event_id: str):
    chain = global_event_federation_runtime.causal_chain(event_id)
    if not chain:
        raise HTTPException(status_code=404, detail="event_id not found in global event store")
    return {"event_id": event_id, "depth": len(chain), "chain": chain}


@router.get("/global/events/replay")
def global_event_replay(correlation_id: Optional[str] = None):
    return global_event_federation_runtime.replay(correlation_id=correlation_id)


@router.get("/global/events/verify")
def global_event_verify(correlation_id: Optional[str] = None):
    return global_event_federation_runtime.verify(correlation_id=correlation_id)


@router.get("/global/events/routes")
def global_event_routes():
    return {
        "module": "global_event_federation",
        "prefix": "/global/events",
        "routes": [
            "POST /global/events",
            "GET /global/events",
            "GET /global/events/causal-chain/{event_id}",
            "GET /global/events/replay",
            "GET /global/events/verify",
            "GET /global/events/routes",
        ],
    }

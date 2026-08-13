from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def decision_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "decision_intelligence_gateway",
        "prefix": "/gateway/decision-intelligence",
        "routes": [
            "GET /gateway/decision-intelligence/routes",
            "GET /gateway/decision-intelligence/health",
            "GET /gateway/decision-intelligence/system-state?portfolio=&project_id=",
            "GET /gateway/decision-intelligence/events/published",
            "POST /gateway/decision-intelligence/decisions/log",
            "GET /gateway/decision-intelligence/decisions/{decision_id}/explain?question=",
            "POST /gateway/decision-intelligence/simulate",
        ],
    }


def _resolve_decision_base_url() -> str:
    configured = (settings.URL_DECISION_INTELLIGENCE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_CEA_INVEST.rstrip("/")


async def _request_decision(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_decision_base_url()
    target = f"{base_url}{path}"
    request_method = method.upper()

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.request(
                request_method,
                target,
                json=payload if request_method != "GET" else None,
                params=params,
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Decision gateway unavailable: {exc}") from exc

    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text}

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=data)

    return {
        "status": "proxied",
        "target": target,
        "http_status": response.status_code,
        "result": data,
    }


@router.get("/health")
async def decision_health() -> Dict[str, Any]:
    return await _request_decision("GET", "/api/v1/decision-intelligence/health")


@router.get("/system-state")
async def decision_system_state(portfolio: str = Query(""), project_id: str = Query("")) -> Dict[str, Any]:
    return await _request_decision(
        "GET",
        "/api/v1/decision-intelligence/system-state",
        params={"portfolio": portfolio, "project_id": project_id},
    )


@router.post("/decisions/log")
async def decision_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_decision("POST", "/api/v1/decision-intelligence/decisions/log", payload=payload)


@router.get("/decisions/{decision_id}/explain")
async def decision_explain(decision_id: str, question: str = Query("")) -> Dict[str, Any]:
    return await _request_decision(
        "GET",
        f"/api/v1/decision-intelligence/decisions/{decision_id}/explain",
        params={"question": question},
    )


@router.post("/simulate")
async def decision_simulate(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_decision("POST", "/api/v1/decision-intelligence/simulate", payload=payload)


@router.get("/events/published")
async def decision_published_events() -> Dict[str, Any]:
    return await _request_decision("GET", "/api/v1/decision-intelligence/events/published")

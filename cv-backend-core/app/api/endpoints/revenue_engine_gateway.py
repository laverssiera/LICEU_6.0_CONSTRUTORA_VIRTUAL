from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def revenue_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "revenue_engine_gateway",
        "prefix": "/gateway/revenue-engine",
        "routes": [
            "GET /gateway/revenue-engine/routes",
            "GET /gateway/revenue-engine/health",
            "GET /gateway/revenue-engine/dashboard",
            "GET /gateway/revenue-engine/events/published",
            "GET /gateway/revenue-engine/pipeline/forecast?portfolio=",
            "POST /gateway/revenue-engine/leads/score",
            "POST /gateway/revenue-engine/leads/close-to-project",
        ],
    }


def _resolve_revenue_base_url() -> str:
    configured = (settings.URL_REVENUE_ENGINE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_OPERA.rstrip("/")


async def _request_revenue(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_revenue_base_url()
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
        raise HTTPException(status_code=502, detail=f"Revenue gateway unavailable: {exc}") from exc

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
async def revenue_health() -> Dict[str, Any]:
    return await _request_revenue("GET", "/api/v1/revenue/health")


@router.get("/dashboard")
async def revenue_dashboard() -> Dict[str, Any]:
    return await _request_revenue("GET", "/api/v1/revenue/dashboard")


@router.get("/events/published")
async def revenue_events() -> Dict[str, Any]:
    return await _request_revenue("GET", "/api/v1/revenue/events/published")


@router.get("/pipeline/forecast")
async def revenue_forecast(portfolio: str = Query("")) -> Dict[str, Any]:
    return await _request_revenue("GET", "/api/v1/revenue/pipeline/forecast", params={"portfolio": portfolio})


@router.post("/leads/score")
async def revenue_score(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_revenue("POST", "/api/v1/revenue/leads/score", payload=payload)


@router.post("/leads/close-to-project")
async def revenue_close_to_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_revenue("POST", "/api/v1/revenue/leads/close-to-project", payload=payload)

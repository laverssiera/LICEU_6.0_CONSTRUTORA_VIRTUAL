from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def execution_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "execution_engine_gateway",
        "prefix": "/gateway/execution-engine",
        "routes": [
            "GET /gateway/execution-engine/routes",
            "GET /gateway/execution-engine/health",
            "GET /gateway/execution-engine/templates?category=",
            "GET /gateway/execution-engine/dashboard?portfolio=&project_id=",
            "GET /gateway/execution-engine/events/published",
            "POST /gateway/execution-engine/templates",
            "POST /gateway/execution-engine/processes/start",
            "POST /gateway/execution-engine/processes/update",
            "POST /gateway/execution-engine/monitor/signal",
        ],
    }


def _resolve_execution_base_url() -> str:
    configured = (settings.URL_EXECUTION_ENGINE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_OPERA.rstrip("/")


async def _request_execution(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_execution_base_url()
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
        raise HTTPException(status_code=502, detail=f"Execution gateway unavailable: {exc}") from exc

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
async def execution_health() -> Dict[str, Any]:
    return await _request_execution("GET", "/api/v1/execution/health")


@router.get("/templates")
async def execution_templates(category: str = Query("")) -> Dict[str, Any]:
    return await _request_execution("GET", "/api/v1/execution/templates", params={"category": category})


@router.post("/templates")
async def execution_create_template(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_execution("POST", "/api/v1/execution/templates", payload=payload)


@router.post("/processes/start")
async def execution_start_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_execution("POST", "/api/v1/execution/processes/start", payload=payload)


@router.post("/processes/update")
async def execution_update_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_execution("POST", "/api/v1/execution/processes/update", payload=payload)


@router.post("/monitor/signal")
async def execution_monitor_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_execution("POST", "/api/v1/execution/monitor/signal", payload=payload)


@router.get("/dashboard")
async def execution_dashboard(portfolio: str = Query(""), project_id: str = Query("")) -> Dict[str, Any]:
    return await _request_execution(
        "GET",
        "/api/v1/execution/dashboard",
        params={"portfolio": portfolio, "project_id": project_id},
    )


@router.get("/events/published")
async def execution_events() -> Dict[str, Any]:
    return await _request_execution("GET", "/api/v1/execution/events/published")

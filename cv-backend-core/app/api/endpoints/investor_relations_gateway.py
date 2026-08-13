from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def ir_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "investor_relations_gateway",
        "prefix": "/gateway/investor-relations",
        "routes": [
            "GET /gateway/investor-relations/routes",
            "GET /gateway/investor-relations/health",
            "GET /gateway/investor-relations/dashboard",
            "GET /gateway/investor-relations/events/published",
            "POST /gateway/investor-relations/investors",
            "POST /gateway/investor-relations/opportunities",
            "POST /gateway/investor-relations/events/consume",
            "POST /gateway/investor-relations/allocations",
            "POST /gateway/investor-relations/performance",
        ],
    }


def _resolve_ir_base_url() -> str:
    configured = (settings.URL_INVESTOR_RELATIONS or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_INVEST_TECH.rstrip("/")


async def _request_ir(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_ir_base_url()
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
        raise HTTPException(status_code=502, detail=f"IR gateway unavailable: {exc}") from exc

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
async def ir_health() -> Dict[str, Any]:
    return await _request_ir("GET", "/api/v1/ir/health")


@router.get("/dashboard")
async def ir_dashboard(investor_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    params = {"investor_id": investor_id} if investor_id else None
    return await _request_ir("GET", "/api/v1/ir/dashboard", params=params)


@router.get("/events/published")
async def ir_published_events() -> Dict[str, Any]:
    return await _request_ir("GET", "/api/v1/ir/events/published")


@router.post("/investors")
async def ir_create_investor(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_ir("POST", "/api/v1/ir/investors", payload=payload)


@router.post("/opportunities")
async def ir_create_opportunity(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_ir("POST", "/api/v1/ir/opportunities", payload=payload)


@router.post("/events/consume")
async def ir_consume_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_ir("POST", "/api/v1/ir/events/consume", payload=payload)


@router.post("/allocations")
async def ir_allocate(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_ir("POST", "/api/v1/ir/allocations", payload=payload)


@router.post("/performance")
async def ir_update_performance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_ir("POST", "/api/v1/ir/performance", payload=payload)
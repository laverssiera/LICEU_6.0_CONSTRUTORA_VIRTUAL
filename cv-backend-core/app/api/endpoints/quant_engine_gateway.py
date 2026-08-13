from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def quant_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "quant_engine_gateway",
        "prefix": "/gateway/quant-engine",
        "routes": [
            "GET /gateway/quant-engine/routes",
            "GET /gateway/quant-engine/health",
            "GET /gateway/quant-engine/dashboard",
            "GET /gateway/quant-engine/events/published",
            "POST /gateway/quant-engine/allocate",
            "POST /gateway/quant-engine/rebalance",
        ],
    }


def _resolve_quant_base_url() -> str:
    configured = (settings.URL_QUANT_ENGINE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_ECONO_TECH.rstrip("/")


async def _request_quant(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_quant_base_url()
    target = f"{base_url}{path}"
    request_method = method.upper()

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.request(
                request_method,
                target,
                json=payload if request_method != "GET" else None,
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Quant gateway unavailable: {exc}") from exc

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
async def quant_health() -> Dict[str, Any]:
    return await _request_quant("GET", "/api/v1/quant/health")


@router.get("/dashboard")
async def quant_dashboard() -> Dict[str, Any]:
    return await _request_quant("GET", "/api/v1/quant/dashboard")


@router.get("/events/published")
async def quant_published_events() -> Dict[str, Any]:
    return await _request_quant("GET", "/api/v1/quant/events/published")


@router.post("/allocate")
async def quant_allocate(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_quant("POST", "/api/v1/quant/allocate", payload=payload)


@router.post("/rebalance")
async def quant_rebalance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_quant("POST", "/api/v1/quant/rebalance", payload=payload)
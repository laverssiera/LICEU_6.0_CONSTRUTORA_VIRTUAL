from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def capital_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "capital_engine_gateway",
        "prefix": "/gateway/capital-engine",
        "routes": [
            "GET /gateway/capital-engine/routes",
            "GET /gateway/capital-engine/health",
            "GET /gateway/capital-engine/funds",
            "GET /gateway/capital-engine/dashboard",
            "GET /gateway/capital-engine/events/published",
            "POST /gateway/capital-engine/funds/subscribe",
            "POST /gateway/capital-engine/indices/recalculate",
            "POST /gateway/capital-engine/quant-lex/sync",
        ],
    }


def _resolve_capital_base_url() -> str:
    configured = (settings.URL_CAPITAL_ENGINE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_CEA_INVEST.rstrip("/")


async def _request_capital(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_capital_base_url()
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
        raise HTTPException(status_code=502, detail=f"Capital gateway unavailable: {exc}") from exc

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
async def capital_health() -> Dict[str, Any]:
    return await _request_capital("GET", "/api/v1/capital/health")


@router.get("/funds")
async def capital_funds() -> Dict[str, Any]:
    return await _request_capital("GET", "/api/v1/capital/funds")


@router.post("/funds/subscribe")
async def capital_subscribe(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_capital("POST", "/api/v1/capital/funds/subscribe", payload=payload)


@router.post("/indices/recalculate")
async def capital_recalculate_indices() -> Dict[str, Any]:
    return await _request_capital("POST", "/api/v1/capital/indices/recalculate")


@router.post("/quant-lex/sync")
async def capital_quant_lex_sync(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_capital("POST", "/api/v1/capital/quant-lex/sync", payload=payload)


@router.get("/dashboard")
async def capital_dashboard() -> Dict[str, Any]:
    return await _request_capital("GET", "/api/v1/capital/dashboard")


@router.get("/events/published")
async def capital_events() -> Dict[str, Any]:
    return await _request_capital("GET", "/api/v1/capital/events/published")

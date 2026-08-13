from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def econotech_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "econotech_gateway",
        "prefix": "/gateway/econotech",
        "routes": [
            "GET /gateway/econotech/routes",
            "GET /gateway/econotech/health",
            "GET /gateway/econotech/dashboard?portfolio=&project_id=",
            "GET /gateway/econotech/events/published",
            "GET /gateway/econotech/john/debate",
            "POST /gateway/econotech/macro/ingest",
            "POST /gateway/econotech/analysis",
            "POST /gateway/econotech/projects/impact",
            "POST /gateway/econotech/quant/adjust",
            "POST /gateway/econotech/lex/reprice",
            "POST /gateway/econotech/esg/score",
            "POST /gateway/econotech/radar/opportunities",
            "POST /gateway/econotech/scenarios/forecast",
            "POST /gateway/econotech/stress/systemic",
        ],
    }


def _resolve_econotech_base_url() -> str:
    configured = (settings.URL_ECONO_TECH or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_CEFEIDA.rstrip("/")


async def _request_econotech(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_econotech_base_url()
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
        raise HTTPException(status_code=502, detail=f"Econotech gateway unavailable: {exc}") from exc

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
async def econotech_health() -> Dict[str, Any]:
    return await _request_econotech("GET", "/api/v1/econotech/health")


@router.post("/macro/ingest")
async def econotech_ingest(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/macro/ingest", payload=payload)


@router.post("/analysis")
async def econotech_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/analysis", payload=payload)


@router.post("/projects/impact")
async def econotech_project_impact(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/projects/impact", payload=payload)


@router.post("/quant/adjust")
async def econotech_quant_adjust(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/quant/adjust", payload=payload)


@router.post("/lex/reprice")
async def econotech_lex_reprice(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/lex/reprice", payload=payload)


@router.get("/john/debate")
async def econotech_john_debate() -> Dict[str, Any]:
    return await _request_econotech("GET", "/api/v1/econotech/john/debate")


@router.post("/esg/score")
async def econotech_esg(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/esg/score", payload=payload)


@router.post("/radar/opportunities")
async def econotech_radar(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/radar/opportunities", payload=payload)


@router.post("/scenarios/forecast")
async def econotech_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/scenarios/forecast", payload=payload)


@router.post("/stress/systemic")
async def econotech_systemic_stress(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_econotech("POST", "/api/v1/econotech/stress/systemic", payload=payload)


@router.get("/dashboard")
async def econotech_dashboard(portfolio: str = Query(""), project_id: str = Query("")) -> Dict[str, Any]:
    return await _request_econotech(
        "GET",
        "/api/v1/econotech/dashboard",
        params={"portfolio": portfolio, "project_id": project_id},
    )


@router.get("/events/published")
async def econotech_events() -> Dict[str, Any]:
    return await _request_econotech("GET", "/api/v1/econotech/events/published")

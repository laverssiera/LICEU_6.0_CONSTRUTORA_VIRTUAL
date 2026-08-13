from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def trust_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "trust_layer_gateway",
        "prefix": "/gateway/trust-layer",
        "routes": [
            "GET /gateway/trust-layer/routes",
            "GET /gateway/trust-layer/health",
            "GET /gateway/trust-layer/audit?company_id=&limit=",
            "GET /gateway/trust-layer/dashboard?company_id=",
            "GET /gateway/trust-layer/events/published",
            "POST /gateway/trust-layer/audit/log",
            "POST /gateway/trust-layer/health-score",
            "POST /gateway/trust-layer/compliance/check",
        ],
    }


def _resolve_trust_base_url() -> str:
    configured = (settings.URL_TRUST_LAYER or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_JURIDICO.rstrip("/")


async def _request_trust(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_trust_base_url()
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
        raise HTTPException(status_code=502, detail=f"Trust gateway unavailable: {exc}") from exc

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
async def trust_health() -> Dict[str, Any]:
    return await _request_trust("GET", "/api/v1/trust/health")


@router.post("/audit/log")
async def trust_audit_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_trust("POST", "/api/v1/trust/audit/log", payload=payload)


@router.get("/audit")
async def trust_audit_list(company_id: str = Query(""), limit: int = Query(50)) -> Dict[str, Any]:
    return await _request_trust("GET", "/api/v1/trust/audit", params={"company_id": company_id, "limit": limit})


@router.post("/health-score")
async def trust_health_score(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_trust("POST", "/api/v1/trust/health-score", payload=payload)


@router.post("/compliance/check")
async def trust_compliance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_trust("POST", "/api/v1/trust/compliance/check", payload=payload)


@router.get("/dashboard")
async def trust_dashboard(company_id: str = Query("")) -> Dict[str, Any]:
    return await _request_trust("GET", "/api/v1/trust/dashboard", params={"company_id": company_id})


@router.get("/events/published")
async def trust_events() -> Dict[str, Any]:
    return await _request_trust("GET", "/api/v1/trust/events/published")

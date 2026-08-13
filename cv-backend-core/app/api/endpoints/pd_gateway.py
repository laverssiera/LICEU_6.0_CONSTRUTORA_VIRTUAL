from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def pd_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "pd_gateway",
        "prefix": "/gateway/pd",
        "routes": [
            "GET /gateway/pd/routes",
            "GET /gateway/pd/health",
            "GET /gateway/pd/dashboard?process_name=",
            "GET /gateway/pd/executions?process_id=&status=&limit=",
            "GET /gateway/pd/processes/versions?process_name=&limit=",
            "GET /gateway/pd/processes/compare?process_name=&from_version=&to_version=",
            "GET /gateway/pd/events/published",
            "POST /gateway/pd/processes",
            "POST /gateway/pd/processes/dsl",
            "POST /gateway/pd/processes/version",
            "POST /gateway/pd/processes/apply",
            "POST /gateway/pd/processes/audit-improvement",
            "POST /gateway/pd/processes/simulate",
            "POST /gateway/pd/processes/run",
            "POST /gateway/pd/processes/audit-validate",
            "POST /gateway/pd/processes/john-interpret",
            "POST /gateway/pd/processes/metrics",
        ],
    }


def _resolve_pd_base_url() -> str:
    configured = (settings.URL_PD_ENGINE or "").strip()
    if configured:
        return configured.rstrip("/")
    fallback = (settings.URL_PD_IA or "").strip()
    if fallback:
        return fallback.rstrip("/")
    return settings.URL_CEFEIDA.rstrip("/")


async def _request_pd(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_pd_base_url()
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
        raise HTTPException(status_code=502, detail=f"PD gateway unavailable: {exc}") from exc

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
async def pd_health() -> Dict[str, Any]:
    return await _request_pd("GET", "/api/v1/pd/health")


@router.post("/processes")
async def pd_define_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes", payload=payload)


@router.post("/processes/dsl")
async def pd_define_process_dsl(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/dsl", payload=payload)


@router.post("/processes/version")
async def pd_version_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/version", payload=payload)


@router.post("/processes/apply")
async def pd_apply_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/apply", payload=payload)


@router.post("/processes/audit-improvement")
async def pd_audit_improvement(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/audit-improvement", payload=payload)


@router.post("/processes/simulate")
async def pd_simulate_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/simulate", payload=payload)


@router.post("/processes/run")
async def pd_run_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/run", payload=payload)


@router.post("/processes/audit-validate")
async def pd_validate_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/audit-validate", payload=payload)


@router.post("/processes/john-interpret")
async def pd_john_interpret(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/john-interpret", payload=payload)


@router.post("/processes/metrics")
async def pd_process_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_pd("POST", "/api/v1/pd/processes/metrics", payload=payload)


@router.get("/dashboard")
async def pd_dashboard(process_name: str = Query("")) -> Dict[str, Any]:
    return await _request_pd("GET", "/api/v1/pd/dashboard", params={"process_name": process_name})


@router.get("/executions")
async def pd_executions(
    process_id: str = Query(""),
    status: str = Query(""),
    limit: int = Query(20),
) -> Dict[str, Any]:
    return await _request_pd(
        "GET",
        "/api/v1/pd/executions",
        params={"process_id": process_id, "status": status, "limit": limit},
    )


@router.get("/processes/versions")
async def pd_versions(process_name: str = Query(""), limit: int = Query(20)) -> Dict[str, Any]:
    return await _request_pd(
        "GET",
        "/api/v1/pd/processes/versions",
        params={"process_name": process_name, "limit": limit},
    )


@router.get("/processes/compare")
async def pd_compare(
    process_name: str = Query(""),
    from_version: str = Query(""),
    to_version: str = Query(""),
) -> Dict[str, Any]:
    return await _request_pd(
        "GET",
        "/api/v1/pd/processes/compare",
        params={"process_name": process_name, "from_version": from_version, "to_version": to_version},
    )


@router.get("/events/published")
async def pd_events() -> Dict[str, Any]:
    return await _request_pd("GET", "/api/v1/pd/events/published")
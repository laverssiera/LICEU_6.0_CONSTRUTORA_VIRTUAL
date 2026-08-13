from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings


router = APIRouter()


@router.get("/routes")
async def lex_routes() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "liceu_exchange_gateway",
        "prefix": "/gateway/lex",
        "routes": [
            "GET /gateway/lex/routes",
            "GET /gateway/lex/health",
            "GET /gateway/lex/dashboard",
            "GET /gateway/lex/events/published",
            "GET /gateway/lex/pricing/fair",
            "GET /gateway/lex/market-maker/{asset_id}?confidence=0.6",
            "GET /gateway/lex/funds",
            "GET /gateway/lex/john/market-brief?index_code=LEX-INFRA",
            "POST /gateway/lex/kyc/{investor_id}",
            "POST /gateway/lex/assets/tokenize",
            "POST /gateway/lex/assets/derived",
            "POST /gateway/lex/clearing/cash/deposit",
            "POST /gateway/lex/clearing/inventory/grant",
            "POST /gateway/lex/quant/sync",
            "POST /gateway/lex/orders",
            "POST /gateway/lex/matching/{asset_id}",
            "POST /gateway/lex/market-maker/{asset_id}/maintain",
            "POST /gateway/lex/indices/recalculate",
            "POST /gateway/lex/indices/tokenize",
            "POST /gateway/lex/funds/subscribe",
            "POST /gateway/lex/funds/tokenize",
        ],
    }


def _resolve_lex_base_url() -> str:
    configured = (settings.URL_LICEU_EXCHANGE or "").strip()
    if configured:
        return configured.rstrip("/")
    return settings.URL_CEA_INVEST.rstrip("/")


async def _request_lex(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _resolve_lex_base_url()
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
        raise HTTPException(status_code=502, detail=f"LEX gateway unavailable: {exc}") from exc

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
async def lex_health() -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/health")


@router.get("/dashboard")
async def lex_dashboard() -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/dashboard")


@router.get("/events/published")
async def lex_published_events() -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/events/published")


@router.get("/pricing/fair")
async def lex_fair_price(roi: float = Query(...), risk: float = Query(...), progress: float = Query(...)) -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/pricing/fair", params={"roi": roi, "risk": risk, "progress": progress})


@router.post("/kyc/{investor_id}")
async def lex_approve_kyc(investor_id: str) -> Dict[str, Any]:
    return await _request_lex("POST", f"/api/v1/lex/kyc/{investor_id}")


@router.post("/assets/tokenize")
async def lex_tokenize_asset(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/assets/tokenize", payload=payload)


@router.post("/assets/derived")
async def lex_create_derived_asset(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/assets/derived", payload=payload)


@router.post("/clearing/cash/deposit")
async def lex_deposit_cash(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/clearing/cash/deposit", payload=payload)


@router.post("/clearing/inventory/grant")
async def lex_grant_inventory(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/clearing/inventory/grant", payload=payload)


@router.post("/quant/sync")
async def lex_sync_quant(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/quant/sync", payload=payload)


@router.post("/orders")
async def lex_place_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/orders", payload=payload)


@router.post("/matching/{asset_id}")
async def lex_run_matching(asset_id: str) -> Dict[str, Any]:
    return await _request_lex("POST", f"/api/v1/lex/matching/{asset_id}")


@router.get("/market-maker/{asset_id}")
async def lex_market_maker_quote(asset_id: str, confidence: float = Query(0.6)) -> Dict[str, Any]:
    return await _request_lex("GET", f"/api/v1/lex/market-maker/{asset_id}", params={"confidence": confidence})


@router.post("/market-maker/{asset_id}/maintain")
async def lex_market_maker_maintain(asset_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", f"/api/v1/lex/market-maker/{asset_id}/maintain", payload=payload)


@router.post("/indices/recalculate")
async def lex_recalculate_indices() -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/indices/recalculate")


@router.post("/indices/tokenize")
async def lex_tokenize_indices() -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/indices/tokenize")


@router.get("/funds")
async def lex_list_funds() -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/funds")


@router.post("/funds/subscribe")
async def lex_subscribe_fund(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/funds/subscribe", payload=payload)


@router.post("/funds/tokenize")
async def lex_tokenize_funds() -> Dict[str, Any]:
    return await _request_lex("POST", "/api/v1/lex/funds/tokenize")


@router.get("/john/market-brief")
async def lex_john_market_brief(index_code: str = Query("LEX-INFRA")) -> Dict[str, Any]:
    return await _request_lex("GET", "/api/v1/lex/john/market-brief", params={"index_code": index_code})
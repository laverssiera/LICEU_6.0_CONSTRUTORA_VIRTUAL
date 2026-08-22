#!/usr/bin/env python3
"""
CROSS_WORKSPACE_CANONICAL_FEDERATION gate executor.

Valida acesso externo via API HTTPS ao Canonical Event Store existente
(liceu_core_os.public.events) sem expor credenciais de PostgreSQL.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests


W89A_EVENT_TYPE = "artifacts.w89_a.registered.v1"
W89B_EVENT_TYPE = "artifacts.w89_b.validated.v1"
W90_HINTS = (
    "w90",
    "event.consumed",
    "consumer",
    "consumption",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_api_url() -> str | None:
    explicit = os.getenv("CANONICAL_EVENT_STORE_API_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")

    codespace_name = os.getenv("CODESPACE_NAME", "").strip()
    forwarding_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "").strip()
    if codespace_name and forwarding_domain:
        return f"https://{codespace_name}-8000.{forwarding_domain}"

    return None


def is_external_url(url: str | None) -> bool:
    if not url:
        return False
    normalized = url.lower()
    return normalized.startswith("https://") and "localhost" not in normalized and "127.0.0.1" not in normalized


def tunnel_headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        return {}
    return {"X-GitHub-Token": token}


def safe_json(resp: requests.Response) -> dict[str, Any]:
    try:
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {"value": data}
    except Exception:
        return {"raw": resp.text}


def login(base_url: str, username: str, password: str, portal: str = "workspace") -> tuple[str | None, str | None]:
    try:
        resp = requests.post(
            f"{base_url}/auth/sso/login",
            json={"username": username, "password": password, "portal": portal},
            headers=tunnel_headers(),
            timeout=15,
        )
    except Exception as exc:
        return None, f"login_exception:{exc}"

    if resp.status_code != 200:
        return None, f"login_failed:{resp.status_code}:{resp.text}"

    token = safe_json(resp).get("access_token")
    if not token:
        return None, "login_missing_access_token"
    return str(token), None


def get_json(base_url: str, path: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    merged_headers = {**tunnel_headers(), **(headers or {})}
    resp = requests.get(f"{base_url}{path}", headers=merged_headers, params=params or {}, timeout=20)
    return resp.status_code, safe_json(resp)


def post_json(base_url: str, path: str, body: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    merged_headers = {**tunnel_headers(), **(headers or {})}
    resp = requests.post(f"{base_url}{path}", json=body, headers=merged_headers, timeout=20)
    return resp.status_code, safe_json(resp)


def extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    if isinstance(payload.get("item"), dict):
        return [payload["item"]]
    return []


def contains_w90_marker(event: dict[str, Any]) -> bool:
    blob = json.dumps(event, ensure_ascii=True).lower()
    return any(marker in blob for marker in W90_HINTS)


def main() -> int:
    api_url = resolve_api_url()

    result: dict[str, Any] = {
        "gate": "CROSS_WORKSPACE_CANONICAL_FEDERATION",
        "timestamp": utc_now(),
        "transport": "https_api",
        "canonical_store": "liceu_core_os.public.events",
        "CANONICAL_EVENT_STORE_API_URL": api_url,
        "external_api_reachable": False,
        "canonical_read_valid": False,
        "canonical_publish_valid": False,
        "w89a_visible": False,
        "w89b_visible": False,
        "w90_visible": False,
        "contract_valid": False,
        "lineage_valid": False,
        "audit_valid": False,
        "consumer_visibility_valid": False,
        "consumer_configuration_variable": "CANONICAL_EVENT_STORE_API_URL",
        "status": "BLOCKED",
        "missing_component": None,
        "errors": [],
        "evidence": {},
    }

    if not api_url:
        result["missing_component"] = "Public API URL resolver (CODESPACE_NAME/GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN or CANONICAL_EVENT_STORE_API_URL)"
        result["errors"].append("external_url_not_resolved")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # 1) Health público
    try:
        health_code, health_payload = get_json(api_url, "/health")
    except Exception as exc:
        result["missing_component"] = "External HTTPS gateway/port-forward for leme-core"
        result["errors"].append(f"external_health_exception:{exc}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result["evidence"]["health"] = {"status_code": health_code, "payload": health_payload}
    result["external_api_reachable"] = bool(health_code == 200 and is_external_url(api_url))

    token, login_error = login(api_url, username=os.getenv("LICEU_GATE_USER", "executivo_demo"), password=os.getenv("LICEU_GATE_PASSWORD", "demo123"))
    if login_error:
        result["missing_component"] = "SSO authentication endpoint/token provisioning"
        result["errors"].append(login_error)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    headers = {"Authorization": f"Bearer {token}"}

    # 2) Health da interface federada
    fed_health_code, fed_health_payload = get_json(api_url, "/federation/events/health", headers=headers)
    result["evidence"]["federation_health"] = {"status_code": fed_health_code, "payload": fed_health_payload}
    if fed_health_code != 200:
        result["missing_component"] = "Federation external API layer (/federation/events/*)"
        result["errors"].append("federation_events_health_unavailable")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # 3) Buscar W89-A / W89-B
    code_w89a, payload_w89a = get_json(api_url, f"/federation/events/by-type/{W89A_EVENT_TYPE}", headers=headers, params={"limit": 200})
    code_w89b, payload_w89b = get_json(api_url, f"/federation/events/by-type/{W89B_EVENT_TYPE}", headers=headers, params={"limit": 200})
    events_w89a = extract_items(payload_w89a) if code_w89a == 200 else []
    events_w89b = extract_items(payload_w89b) if code_w89b == 200 else []

    result["w89a_visible"] = len(events_w89a) > 0
    result["w89b_visible"] = len(events_w89b) > 0

    # 4) Leitura canônica + varredura W90
    code_all, payload_all = get_json(api_url, "/federation/events", headers=headers, params={"limit": 2000})
    all_events = extract_items(payload_all) if code_all == 200 else []
    result["canonical_read_valid"] = bool(code_all == 200 and len(all_events) > 0)

    w90_events = [event for event in all_events if contains_w90_marker(event)]
    result["w90_visible"] = len(w90_events) > 0

    # 5) Publicar artefato canônico de prova
    source_for_lineage = events_w89a[0] if events_w89a else (all_events[0] if all_events else None)
    publish_body = {
        "event_type": "federation.cross_workspace.probe.v1",
        "source": "cross_workspace_gate",
        "payload": {
            "artifact_class": "CROSS_WORKSPACE_PROBE",
            "note": "External canonical publication probe",
            "gate": "CROSS_WORKSPACE_CANONICAL_FEDERATION",
        },
        "source_event_id": source_for_lineage.get("event_id") if source_for_lineage else None,
        "trace_id": f"trace-cross-workspace-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "artifact_id": f"W90-CROSS-WORKSPACE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "scope": "federation",
        "producer": "cross_workspace_gate",
        "contract_id": "federation.cross_workspace.probe.v1",
        "contract_version": "1.0.0",
    }

    publish_code, publish_payload = post_json(api_url, "/federation/events/publish", body=publish_body, headers=headers)
    result["evidence"]["publish"] = {"status_code": publish_code, "payload": publish_payload}

    result["canonical_publish_valid"] = publish_code == 200
    result["contract_valid"] = bool((publish_payload.get("contract_validation") or {}).get("valid")) if publish_code == 200 else False

    published_event = publish_payload.get("event") if isinstance(publish_payload.get("event"), dict) else None
    if published_event and contains_w90_marker(published_event):
        result["w90_visible"] = True

    lineage_signal = False
    if publish_code == 200:
        lineage_data = publish_payload.get("lineage_validation") or {}
        lineage_signal = bool(lineage_data.get("valid"))

    # Link W89-B -> W89-A via payload.parent_artifact_id (canônico atual)
    w89a_artifact_ids = {str(item.get("artifact_id")) for item in events_w89a if item.get("artifact_id")}
    linkage_pairs = 0
    for item in events_w89b:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        parent_artifact_id = payload.get("parent_artifact_id")
        if parent_artifact_id and parent_artifact_id in w89a_artifact_ids:
            linkage_pairs += 1

    result["lineage_valid"] = bool(lineage_signal or linkage_pairs > 0)

    # 6) Audit metadata
    audit_code, audit_payload = get_json(api_url, "/audit/events", headers=headers, params={"limit": 200, "source": "canonical_event_store"})
    audit_items = extract_items(audit_payload) if audit_code == 200 else []
    result["audit_valid"] = bool(audit_code == 200 and len(audit_items) > 0)
    result["evidence"]["audit"] = {
        "status_code": audit_code,
        "total": len(audit_items),
        "sample": audit_items[:3],
    }

    # 7) Consumer visibility
    config_code, config_payload = get_json(api_url, "/federation/events/config", headers=headers)
    config_var_ok = bool(
        config_code == 200
        and config_payload.get("consumer_configuration_variable") == "CANONICAL_EVENT_STORE_API_URL"
    )
    result["consumer_visibility_valid"] = bool(result["external_api_reachable"] and config_var_ok and result["canonical_read_valid"])
    result["evidence"]["config"] = {"status_code": config_code, "payload": config_payload}

    checks = [
        result["external_api_reachable"],
        result["canonical_read_valid"],
        result["canonical_publish_valid"],
        result["w89a_visible"],
        result["w89b_visible"],
        result["w90_visible"],
        result["contract_valid"],
        result["lineage_valid"],
        result["audit_valid"],
        result["consumer_visibility_valid"],
    ]

    if all(checks):
        result["status"] = "PASS"
        result["missing_component"] = None
    else:
        result["status"] = "BLOCKED"
        if not result["external_api_reachable"]:
            result["missing_component"] = "External HTTPS API reachability"
        elif not result["w90_visible"]:
            result["missing_component"] = "Canonical W90 artifact/event publication not present in event stream"
        elif not result["audit_valid"]:
            result["missing_component"] = "Audit metadata visibility via API"
        else:
            result["missing_component"] = "One or more canonical federation validations failed"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

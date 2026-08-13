import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="LICEU Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SERVICE_URLS = {
    "liceu_core": "http://liceu_core:8000",
    "opera": "http://opera:8000",
    "hub": "http://hub:8000",
    "audit_hospital": "http://audit_hospital:8000",
    "pd": "http://pd:8000",
    "fornecedores": "http://fornecedores:8000",
    "john_engine": "http://john_engine:8000",
}


async def _fetch_json(service: str, path: str, method: str = "GET", json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{SERVICE_URLS[service]}{path}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if method == "POST":
                response = await client.post(url, json=json_payload or {})
            else:
                response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"items": payload}
    except Exception:
        return {}


async def _execute_core_action(path: str) -> dict[str, Any]:
    if path.startswith("/actions/approve-business/"):
        business_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("liceu_core", f"/approve/{business_id}", method="POST")
    if path.startswith("/actions/pause-project/"):
        project_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("opera", f"/actions/pause/{project_id}", method="POST")
    if path.startswith("/actions/release-payment/"):
        project_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("hub", f"/actions/release-payment/{project_id}", method="POST")
    if path.startswith("/actions/trigger-audit/"):
        project_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("audit_hospital", f"/actions/trigger-audit/{project_id}", method="POST")
    if path.startswith("/actions/start-training/"):
        project_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("pd", f"/actions/start-training/{project_id}", method="POST")
    if path.startswith("/actions/reinforce-team/"):
        project_id = path.rsplit("/", 1)[-1]
        return await _fetch_json("opera", f"/actions/reinforce-team/{project_id}", method="POST")
    return {"status": "ignored", "reason": "unknown_target_path", "target_path": path}


@app.on_event("startup")
async def startup() -> None:
    return None


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


@app.get("/dashboard/kpis")
async def dashboard_kpis():
    projects_payload = await _fetch_json("opera", "/state/projects")
    alerts_payload = await _fetch_json("audit_hospital", "/state/alerts")
    finance = await _fetch_json("hub", "/state/finance")

    projects = projects_payload.get("items", []) if isinstance(projects_payload.get("items"), list) else []
    alerts = alerts_payload.get("items", []) if isinstance(alerts_payload.get("items"), list) else []
    dre = finance.get("dre", {}) if isinstance(finance.get("dre"), dict) else {}
    cash_flow = finance.get("cash_flow", {}) if isinstance(finance.get("cash_flow"), dict) else {}
    revenue = dre.get("revenue", 0)
    outflow = cash_flow.get("outflow", 0)
    margin = revenue - outflow
    return {
        "projects": len(projects),
        "active_projects": len([item for item in projects if item["status"] != "paused"]),
        "alerts": len(alerts),
        "health_score": alerts_payload.get("health_score", 0),
        "revenue": revenue,
        "margin": margin,
        "roi": finance.get("roi", 0),
    }


@app.get("/dashboard/pipeline")
async def dashboard_pipeline():
    payload = await _fetch_json("liceu_core", "/state/pipeline")
    items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
    return {"items": items, "total": payload.get("total", len(items))}


@app.get("/dashboard/projects")
async def dashboard_projects():
    payload = await _fetch_json("opera", "/state/projects")
    items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
    return {"items": items, "total": payload.get("total", len(items))}


@app.get("/dashboard/finance")
async def dashboard_finance():
    payload = await _fetch_json("hub", "/state/finance")
    return payload or {"dre": {}, "cash_flow": {}, "roi": 0}


@app.get("/dashboard/alerts")
async def dashboard_alerts(limit: int = 20):
    safe_limit = max(1, min(limit, 200))
    payload = await _fetch_json("audit_hospital", f"/state/alerts?limit={safe_limit}")
    items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
    return {"items": items, "total": payload.get("total", len(items))}


@app.get("/dashboard/events")
async def dashboard_events(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    responses = await asyncio.gather(
        _fetch_json("liceu_core", f"/state/events?limit={safe_limit}"),
        _fetch_json("opera", f"/state/events?limit={safe_limit}"),
        _fetch_json("hub", f"/state/events?limit={safe_limit}"),
        _fetch_json("audit_hospital", f"/state/events?limit={safe_limit}"),
        _fetch_json("pd", f"/state/events?limit={safe_limit}"),
        _fetch_json("fornecedores", f"/state/events?limit={safe_limit}"),
    )
    all_items = []
    for payload in responses:
        items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
        all_items.extend(items)
    all_items.sort(key=lambda item: item.get("timestamp", ""))
    items = all_items[-safe_limit:]
    return {"items": items, "total": len(all_items)}


@app.get("/dashboard/john/suggestions")
async def dashboard_john_suggestions(status: str = "pending", limit: int = 20):
    safe_limit = max(1, min(limit, 200))
    payload = await _fetch_json("john_engine", f"/john/suggestions?status={status}&limit={safe_limit}")
    items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
    return {"items": items, "total": payload.get("total", len(items)), "status": status}


@app.get("/dashboard/john/prediction")
async def dashboard_john_prediction(project_id: str | None = None):
    suffix = f"?project_id={project_id}" if project_id else ""
    payload = await _fetch_json("john_engine", f"/john/predictions/latest{suffix}")
    items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
    if not items:
        return {"item": None}
    return {"item": items[0]}


@app.get("/dashboard/john/portfolio")
async def dashboard_john_portfolio(strategy: str = "equilibrado"):
    latest = await _fetch_json("john_engine", "/john/portfolio/decisions/latest")
    item = latest.get("item") if isinstance(latest.get("item"), dict) else None
    if item is not None and item.get("status") == "pending":
        return {"item": item}

    projects_payload = await _fetch_json("opera", "/state/projects")
    finance_payload = await _fetch_json("hub", "/state/finance")
    projects = projects_payload.get("items", []) if isinstance(projects_payload.get("items"), list) else []
    cash_flow = finance_payload.get("cash_flow", {}) if isinstance(finance_payload.get("cash_flow"), dict) else {}
    available_capital = max(500000.0, float(cash_flow.get("inflow", 0) or 0) - float(cash_flow.get("outflow", 0) or 0))

    prepared_projects = []
    for project in projects:
        progress = float(project.get("progress", 0) or 0)
        prepared_projects.append(
            {
                "id": project.get("id"),
                "name": project.get("name", project.get("id")),
                "expected_return": 14 + (progress * 0.12),
                "risk_score": max(10.0, 65.0 - (progress * 0.35)),
                "progress": progress,
                "capital_allocated": float(project.get("tasks_open", 0) or 0) * 50000,
                "required_capital": max(150000.0, (100 - progress) * 15000),
                "status": project.get("status", "active"),
            }
        )

    payload = {
        "portfolio": {
            "name": "LICEU Portfolio",
            "strategy": strategy,
            "capital_total": available_capital,
        },
        "projects": prepared_projects,
    }
    analyzed = await _fetch_json("john_engine", "/john/portfolio/recommendation/analyze", method="POST", json_payload=payload)
    return {"item": analyzed if analyzed else None}


@app.get("/john/suggestions")
async def john_suggestions(status: str = "pending", limit: int = 50):
    return await dashboard_john_suggestions(status=status, limit=limit)


@app.get("/john/predictions/latest")
async def john_predictions_latest(project_id: str | None = None):
    return await dashboard_john_prediction(project_id=project_id)


@app.get("/john/portfolio/decisions/latest")
async def john_portfolio_latest(strategy: str = "equilibrado"):
    return await dashboard_john_portfolio(strategy=strategy)


@app.post("/approve/{business_id}")
async def approve(business_id: str):
    payload = await _fetch_json("liceu_core", f"/approve/{business_id}", method="POST")
    return payload or {"status": "sent", "business_id": business_id}


@app.post("/actions/approve-business/{business_id}")
async def action_approve_business(business_id: str):
    return await approve(business_id)


@app.post("/actions/pause-project/{project_id}")
async def action_pause_project(project_id: str):
    payload = await _fetch_json("opera", f"/actions/pause/{project_id}", method="POST")
    if payload.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Project not found")
    return payload


@app.post("/actions/release-payment/{project_id}")
async def action_release_payment(project_id: str):
    payload = await _fetch_json("hub", f"/actions/release-payment/{project_id}", method="POST")
    return payload


@app.post("/actions/trigger-audit/{project_id}")
async def action_trigger_audit(project_id: str):
    payload = await _fetch_json("audit_hospital", f"/actions/trigger-audit/{project_id}", method="POST")
    return payload


@app.post("/actions/start-training/{project_id}")
async def action_start_training(project_id: str):
    payload = await _fetch_json("pd", f"/actions/start-training/{project_id}", method="POST")
    return payload


@app.post("/actions/john-approve/{suggestion_id}")
async def action_john_approve(suggestion_id: str, payload: dict[str, Any] | None = None):
    # AI never executes directly. Human approval triggers a core action path.
    approved = await _fetch_json(
        "john_engine",
        f"/john/suggestions/{suggestion_id}/approve",
        method="POST",
        json_payload=payload,
    )
    if approved.get("status") != "approved":
        return approved

    target_path = approved.get("target_path", "")
    core_execution = await _execute_core_action(target_path) if target_path else {"status": "ignored", "reason": "missing_target_path"}
    return {
        "status": "approved_and_forwarded",
        "suggestion": approved.get("suggestion"),
        "target_path": target_path,
        "core_execution": core_execution,
    }


@app.post("/john/suggestions/{suggestion_id}/approve")
async def john_approve(suggestion_id: str, payload: dict[str, Any] | None = None):
    return await action_john_approve(suggestion_id, payload)


@app.post("/actions/john-reject/{suggestion_id}")
async def action_john_reject(suggestion_id: str, payload: dict[str, Any] | None = None):
    response = await _fetch_json(
        "john_engine",
        f"/john/suggestions/{suggestion_id}/reject",
        method="POST",
        json_payload=payload,
    )
    return response


@app.post("/john/suggestions/{suggestion_id}/reject")
async def john_reject(suggestion_id: str, payload: dict[str, Any] | None = None):
    return await action_john_reject(suggestion_id, payload)


@app.post("/actions/john-approve-prediction/{prediction_id}")
async def action_john_approve_prediction(prediction_id: str, payload: dict[str, Any] | None = None):
    approved = await _fetch_json(
        "john_engine",
        f"/john/predictions/{prediction_id}/approve",
        method="POST",
        json_payload=payload,
    )
    if approved.get("status") != "approved":
        return approved

    target_path = approved.get("target_path", "")
    core_execution = await _execute_core_action(target_path) if target_path else {"status": "ignored", "reason": "missing_target_path"}
    return {
        "status": "approved_and_forwarded",
        "prediction": approved.get("prediction"),
        "target_path": target_path,
        "core_execution": core_execution,
    }


@app.post("/actions/john-reject-prediction/{prediction_id}")
async def action_john_reject_prediction(prediction_id: str, payload: dict[str, Any] | None = None):
    response = await _fetch_json(
        "john_engine",
        f"/john/predictions/{prediction_id}/reject",
        method="POST",
        json_payload=payload,
    )
    return response


@app.post("/john/predictions/{prediction_id}/approve")
async def john_approve_prediction(prediction_id: str, payload: dict[str, Any] | None = None):
    return await action_john_approve_prediction(prediction_id, payload)


@app.post("/john/predictions/{prediction_id}/reject")
async def john_reject_prediction(prediction_id: str, payload: dict[str, Any] | None = None):
    return await action_john_reject_prediction(prediction_id, payload)


@app.post("/actions/john-approve-portfolio/{decision_id}")
async def action_john_approve_portfolio(decision_id: str, payload: dict[str, Any] | None = None):
    approved = await _fetch_json(
        "john_engine",
        f"/john/portfolio/decisions/{decision_id}/approve",
        method="POST",
        json_payload=payload,
    )
    if approved.get("status") != "approved":
        return approved

    decision = approved.get("decision", {}) if isinstance(approved.get("decision"), dict) else {}
    allocations = decision.get("allocation", []) if isinstance(decision.get("allocation"), list) else []
    executions = []
    for allocation in allocations:
        project_external_id = str(allocation.get("project_external_id") or "")
        if not project_external_id:
            continue
        execution = await _fetch_json("hub", f"/actions/release-payment/{project_external_id}", method="POST")
        executions.append({"project_id": project_external_id, "result": execution})

    return {
        "status": "approved_and_forwarded",
        "decision": decision,
        "core_execution": executions,
    }


@app.post("/actions/john-reject-portfolio/{decision_id}")
async def action_john_reject_portfolio(decision_id: str, payload: dict[str, Any] | None = None):
    response = await _fetch_json(
        "john_engine",
        f"/john/portfolio/decisions/{decision_id}/reject",
        method="POST",
        json_payload=payload,
    )
    return response

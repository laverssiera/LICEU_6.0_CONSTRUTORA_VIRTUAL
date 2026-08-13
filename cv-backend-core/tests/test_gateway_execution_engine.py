from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_execution_routes_discovery_endpoint():
    response = client.get("/gateway/execution-engine/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "execution_engine_gateway"
    assert "POST /gateway/execution-engine/processes/start" in payload["routes"]


def test_gateway_execution_dashboard_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://execution{path}",
            "http_status": 200,
            "result": {"kpis": {"critical_alerts": 1}},
        }

    monkeypatch.setattr("app.api.endpoints.execution_engine_gateway._request_execution", fake_request)

    response = client.get("/gateway/execution-engine/dashboard?portfolio=infra&project_id=P1")

    assert response.status_code == 200
    assert captured["params"] == {"portfolio": "infra", "project_id": "P1"}


def test_gateway_execution_monitor_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://execution{path}",
            "http_status": 200,
            "result": {
                "project_id": payload["project_id"],
                "metric": payload["metric"],
                "level": "yellow",
            },
        }

    monkeypatch.setattr("app.api.endpoints.execution_engine_gateway._request_execution", fake_request)

    response = client.post(
        "/gateway/execution-engine/monitor/signal",
        json={"project_id": "P1", "metric": "delay_days", "value": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["project_id"] == "P1"
    assert payload["result"]["metric"] == "delay_days"


def test_gateway_execution_start_process_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "process_compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.execution_engine_gateway._request_execution", fake_request)

    response = client.post(
        "/gateway/execution-engine/processes/start",
        json={
            "project_id": "P-BLOCK",
            "template_id": "T-1",
            "compliance_status": "fail",
            "health_level": "critical",
            "health_score": 20,
        },
    )

    assert response.status_code == 403


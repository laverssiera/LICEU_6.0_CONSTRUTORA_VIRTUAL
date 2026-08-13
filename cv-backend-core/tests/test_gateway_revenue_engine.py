from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_revenue_routes_discovery_endpoint():
    response = client.get("/gateway/revenue-engine/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "revenue_engine_gateway"
    assert "POST /gateway/revenue-engine/leads/score" in payload["routes"]


def test_gateway_revenue_forecast_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://revenue{path}",
            "http_status": 200,
            "result": {"projected_revenue": 123456.0},
        }

    monkeypatch.setattr("app.api.endpoints.revenue_engine_gateway._request_revenue", fake_request)

    response = client.get("/gateway/revenue-engine/pipeline/forecast?portfolio=infra")

    assert response.status_code == 200
    assert captured["params"] == {"portfolio": "infra"}


def test_gateway_revenue_score_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://revenue{path}",
            "http_status": 200,
            "result": {
                "name": payload["name"],
                "probability": 0.81,
            },
        }

    monkeypatch.setattr("app.api.endpoints.revenue_engine_gateway._request_revenue", fake_request)

    response = client.post(
        "/gateway/revenue-engine/leads/score",
        json={"name": "Lead A", "behavior_score": 0.9, "potential_value": 900000, "portfolio": "infra"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["name"] == "Lead A"
    assert payload["result"]["probability"] == 0.81


def test_gateway_revenue_close_to_project_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "lead_compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.revenue_engine_gateway._request_revenue", fake_request)

    response = client.post(
        "/gateway/revenue-engine/leads/close-to-project",
        json={
            "lead_id": "L-1",
            "project_name": "Projeto Bloqueado",
            "compliance_status": "fail",
            "health_level": "critical",
            "health_score": 25,
        },
    )

    assert response.status_code == 403


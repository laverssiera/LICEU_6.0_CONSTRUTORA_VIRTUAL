from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_econotech_routes_discovery_endpoint():
    response = client.get("/gateway/econotech/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "econotech_gateway"
    assert "POST /gateway/econotech/macro/ingest" in payload["routes"]


def test_gateway_econotech_dashboard_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://econotech{path}",
            "http_status": 200,
            "result": {"kpis": {"macro_pressure": 7.2}},
        }

    monkeypatch.setattr("app.api.endpoints.econotech_gateway._request_econotech", fake_request)

    response = client.get("/gateway/econotech/dashboard?portfolio=infra&project_id=P1")

    assert response.status_code == 200
    assert captured["params"] == {"portfolio": "infra", "project_id": "P1"}


def test_gateway_econotech_analysis_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://econotech{path}",
            "http_status": 200,
            "result": {
                "pressure": 8.1,
                "trend": "moderate_pressure",
            },
        }

    monkeypatch.setattr("app.api.endpoints.econotech_gateway._request_econotech", fake_request)

    response = client.post(
        "/gateway/econotech/analysis",
        json={"inflation": 5.2, "interest": 10.1, "commodity": 7.0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["trend"] == "moderate_pressure"


def test_gateway_econotech_analysis_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "macro_feed_blocked"})

    monkeypatch.setattr("app.api.endpoints.econotech_gateway._request_econotech", fake_request)

    response = client.post(
        "/gateway/econotech/analysis",
        json={"inflation": 5.0, "interest": 9.0, "commodity": 6.0},
    )

    assert response.status_code == 403


def test_gateway_econotech_forecast_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://econotech{path}",
            "http_status": 200,
            "result": {
                "best_scenario": "stability",
                "decision": {"quant": {"action": "selective_allocation"}},
            },
        }

    monkeypatch.setattr("app.api.endpoints.econotech_gateway._request_econotech", fake_request)

    response = client.post(
        "/gateway/econotech/scenarios/forecast",
        json={
            "data": {
                "inflation": 5.5,
                "interest_rate": 12.75,
                "gdp_growth": 2.1,
                "steel_price": 100,
                "cement_price": 80,
                "exchange_rate": 5.1,
                "construction_demand": 0.7,
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["best_scenario"] == "stability"


def test_gateway_econotech_systemic_stress_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://econotech{path}",
            "http_status": 200,
            "result": {
                "system_risk": "HIGH",
                "projects_critical": 5,
                "recommended_action": "DEFENSIVE_MODE",
            },
        }

    monkeypatch.setattr("app.api.endpoints.econotech_gateway._request_econotech", fake_request)

    response = client.post(
        "/gateway/econotech/stress/systemic",
        json={
            "base_data": {
                "interest_rate": 12.75,
                "construction_demand": 0.7,
                "steel_price": 100,
                "cement_price": 80,
                "liquidity": 1.0,
                "confidence": 1.0,
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["system_risk"] == "HIGH"

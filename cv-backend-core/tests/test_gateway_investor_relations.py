from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_ir_routes_discovery_endpoint():
    response = client.get("/gateway/investor-relations/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "investor_relations_gateway"
    assert "GET /gateway/investor-relations/health" in payload["routes"]


def test_gateway_ir_health_forwards_payload(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://ir{path}",
            "http_status": 200,
            "result": {"status": "ok", "module": "investor_relations"},
        }

    monkeypatch.setattr("app.api.endpoints.investor_relations_gateway._request_ir", fake_request)

    response = client.get("/gateway/investor-relations/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "proxied"
    assert payload["result"]["module"] == "investor_relations"


def test_gateway_ir_create_opportunity_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://ir{path}",
            "http_status": 200,
            "result": {
                "project_id": payload["id"],
                "required_capital": payload["required_capital"],
                "risk_level": payload["risk"],
            },
        }

    monkeypatch.setattr("app.api.endpoints.investor_relations_gateway._request_ir", fake_request)

    response = client.post(
        "/gateway/investor-relations/opportunities",
        json={
            "id": "obra-777",
            "approved": True,
            "required_capital": 2_000_000,
            "roi": 30,
            "risk": "moderate",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["project_id"] == "obra-777"
    assert payload["result"]["risk_level"] == "moderate"


def test_gateway_ir_dashboard_passes_query_params(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://ir{path}",
            "http_status": 200,
            "result": {"metrics": {"roi_consolidated": 28}},
        }

    monkeypatch.setattr("app.api.endpoints.investor_relations_gateway._request_ir", fake_request)

    response = client.get("/gateway/investor-relations/dashboard?investor_id=inv-123")

    assert response.status_code == 200
    assert captured["params"] == {"investor_id": "inv-123"}


def test_gateway_ir_create_opportunity_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "company_health_critical"})

    monkeypatch.setattr("app.api.endpoints.investor_relations_gateway._request_ir", fake_request)

    response = client.post(
        "/gateway/investor-relations/opportunities",
        json={
            "id": "obra-999",
            "approved": True,
            "required_capital": 2_000_000,
            "roi": 30,
            "risk": "moderate",
            "health_level": "critical",
            "health_score": 30,
        },
    )

    assert response.status_code == 403

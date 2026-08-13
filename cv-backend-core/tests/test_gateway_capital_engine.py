from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_capital_routes_discovery_endpoint():
    response = client.get("/gateway/capital-engine/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "capital_engine_gateway"
    assert "POST /gateway/capital-engine/quant-lex/sync" in payload["routes"]


def test_gateway_capital_funds_forwards_get(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        return {
            "status": "proxied",
            "target": f"mock://capital{path}",
            "http_status": 200,
            "result": {"count": 4},
        }

    monkeypatch.setattr("app.api.endpoints.capital_engine_gateway._request_capital", fake_request)

    response = client.get("/gateway/capital-engine/funds")

    assert response.status_code == 200
    assert response.json()["result"]["count"] == 4


def test_gateway_capital_sync_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        return {
            "status": "proxied",
            "target": f"mock://capital{path}",
            "http_status": 200,
            "result": {
                "allocation": {"allocations": [{"project_id": "P1"}]},
                "lex_sync": {"count": 1},
            },
        }

    monkeypatch.setattr("app.api.endpoints.capital_engine_gateway._request_capital", fake_request)

    response = client.post(
        "/gateway/capital-engine/quant-lex/sync",
        json={
            "investors": [{"investor_id": "I1", "profile": "moderado", "capital": 1000000, "risk_tolerance": 0.5}],
            "projects": [{"project_id": "P1", "roi": 120, "risk": 0.4, "duration": 18, "capital_required": 500000}],
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["lex_sync"]["count"] == 1


def test_gateway_capital_subscribe_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        raise HTTPException(status_code=403, detail={"detail": "investor_compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.capital_engine_gateway._request_capital", fake_request)

    response = client.post(
        "/gateway/capital-engine/funds/subscribe",
        json={
            "fund_id": "F-1",
            "investor_id": "I-BLOCK",
            "amount": 10000,
            "compliance_status": "fail",
            "health_level": "critical",
            "health_score": 20,
        },
    )

    assert response.status_code == 403

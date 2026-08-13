from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_decision_routes_discovery_endpoint():
    response = client.get("/gateway/decision-intelligence/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "decision_intelligence_gateway"
    assert "POST /gateway/decision-intelligence/simulate" in payload["routes"]


def test_gateway_decision_state_forwards_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://decision{path}",
            "http_status": 200,
            "result": {"kpis": {"decisions_logged": 2}},
        }

    monkeypatch.setattr("app.api.endpoints.decision_intelligence_gateway._request_decision", fake_request)

    response = client.get("/gateway/decision-intelligence/system-state?portfolio=infra&project_id=P1")

    assert response.status_code == 200
    assert captured["params"] == {"portfolio": "infra", "project_id": "P1"}


def test_gateway_decision_log_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://decision{path}",
            "http_status": 200,
            "result": {
                "decision_type": payload["decision_type"],
                "action": payload["action"],
            },
        }

    monkeypatch.setattr("app.api.endpoints.decision_intelligence_gateway._request_decision", fake_request)

    response = client.post(
        "/gateway/decision-intelligence/decisions/log",
        json={
            "decision_type": "allocation",
            "portfolio": "infra",
            "project_id": "P1",
            "action": "approve",
            "outcome": "accepted",
            "inputs": {"roi": 15, "risk": 0.3},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["decision_type"] == "allocation"
    assert payload["result"]["action"] == "approve"


def test_gateway_decision_log_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "decision_compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.decision_intelligence_gateway._request_decision", fake_request)

    response = client.post(
        "/gateway/decision-intelligence/decisions/log",
        json={
            "decision_type": "allocation",
            "portfolio": "infra",
            "project_id": "P-BLOCK",
            "action": "approve",
            "outcome": "accepted",
            "compliance_status": "fail",
            "health_level": "critical",
            "health_score": 30,
        },
    )

    assert response.status_code == 403


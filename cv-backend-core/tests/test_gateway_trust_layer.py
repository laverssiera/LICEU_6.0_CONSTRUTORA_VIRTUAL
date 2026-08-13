from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_trust_routes_discovery_endpoint():
    response = client.get("/gateway/trust-layer/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "trust_layer_gateway"
    assert "POST /gateway/trust-layer/compliance/check" in payload["routes"]


def test_gateway_trust_audit_list_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://trust{path}",
            "http_status": 200,
            "result": {"count": 1, "entries": []},
        }

    monkeypatch.setattr("app.api.endpoints.trust_layer_gateway._request_trust", fake_request)

    response = client.get("/gateway/trust-layer/audit?company_id=C1&limit=20")

    assert response.status_code == 200
    assert captured["params"] == {"company_id": "C1", "limit": 20}


def test_gateway_trust_compliance_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://trust{path}",
            "http_status": 200,
            "result": {"status": "fail", "violations": ["kyc"]},
        }

    monkeypatch.setattr("app.api.endpoints.trust_layer_gateway._request_trust", fake_request)

    response = client.post(
        "/gateway/trust-layer/compliance/check",
        json={"company_id": "C1", "checks": {"kyc": False}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "fail"
    assert "kyc" in payload["result"]["violations"]


def test_gateway_trust_compliance_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.trust_layer_gateway._request_trust", fake_request)

    response = client.post(
        "/gateway/trust-layer/compliance/check",
        json={"company_id": "C-BLOCK", "checks": {"kyc": False}},
    )

    assert response.status_code == 403

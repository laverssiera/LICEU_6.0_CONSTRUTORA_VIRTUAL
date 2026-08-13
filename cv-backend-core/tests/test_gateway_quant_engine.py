from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_quant_routes_discovery_endpoint():
    response = client.get("/gateway/quant-engine/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "quant_engine_gateway"
    assert "POST /gateway/quant-engine/allocate" in payload["routes"]


def test_gateway_quant_health_forwards_payload(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        return {
            "status": "proxied",
            "target": f"mock://quant{path}",
            "http_status": 200,
            "result": {"status": "ok", "module": "quant_engine"},
        }

    monkeypatch.setattr("app.api.endpoints.quant_engine_gateway._request_quant", fake_request)

    response = client.get("/gateway/quant-engine/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "proxied"
    assert payload["result"]["module"] == "quant_engine"


def test_gateway_quant_allocate_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        return {
            "status": "proxied",
            "target": f"mock://quant{path}",
            "http_status": 200,
            "result": {
                "allocations": [
                    {"investor_id": payload["investors"][0]["investor_id"], "project_id": payload["projects"][0]["project_id"]}
                ]
            },
        }

    monkeypatch.setattr("app.api.endpoints.quant_engine_gateway._request_quant", fake_request)

    response = client.post(
        "/gateway/quant-engine/allocate",
        json={
            "investors": [
                {"investor_id": "I1", "profile": "moderado", "capital": 1_000_000, "risk_tolerance": 0.5}
            ],
            "projects": [
                {"project_id": "P1", "roi": 32, "risk": 0.4, "duration": 18, "capital_required": 2_000_000}
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["allocations"][0]["investor_id"] == "I1"
    assert payload["result"]["allocations"][0]["project_id"] == "P1"


def test_gateway_quant_allocate_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None):
        raise HTTPException(status_code=403, detail={"detail": "compliance_failed"})

    monkeypatch.setattr("app.api.endpoints.quant_engine_gateway._request_quant", fake_request)

    response = client.post(
        "/gateway/quant-engine/allocate",
        json={
            "investors": [
                {"investor_id": "I1", "profile": "agressivo", "capital": 1_000_000, "risk_tolerance": 0.8}
            ],
            "projects": [
                {
                    "project_id": "P_BLOCK",
                    "roi": 200,
                    "risk": 0.6,
                    "duration": 12,
                    "capital_required": 2_000_000,
                    "compliance_status": "fail",
                }
            ],
        },
    )

    assert response.status_code == 403


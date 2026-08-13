from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_gateway_pd_routes_discovery_endpoint():
    response = client.get("/gateway/pd/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "pd_gateway"
    assert "POST /gateway/pd/processes/dsl" in payload["routes"]


def test_gateway_pd_dashboard_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://pd{path}",
            "http_status": 200,
            "result": {"processes": [{"name": "Closeout Rain Protocol"}]},
        }

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.get("/gateway/pd/dashboard?process_name=Closeout")

    assert response.status_code == 200
    assert captured["params"] == {"process_name": "Closeout"}


def test_gateway_pd_define_dsl_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://pd{path}",
            "http_status": 200,
            "result": {
                "process": {
                    "name": payload["name"],
                    "version": 1,
                }
            },
        }

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.post(
        "/gateway/pd/processes/dsl",
        json={
            "name": "Closeout Rain Protocol",
            "domain": "obra",
            "dsl": "name: Closeout Rain Protocol\nsteps:\n  - id: vistoria\n    type: checklist",
        },
    )

    assert response.status_code == 200
    assert response.json()["result"]["process"]["name"] == "Closeout Rain Protocol"


def test_gateway_pd_run_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "process_blocked"})

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.post(
        "/gateway/pd/processes/run",
        json={"process_name": "Blocked Process", "context": {"project_id": "P-BLOCK"}},
    )

    assert response.status_code == 403


def test_gateway_pd_john_interpret_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://pd{path}",
            "http_status": 200,
            "result": {
                "insight": {
                    "summary": "Processo pronto para padronizacao global",
                    "recommended_version_bump": True,
                }
            },
        }

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.post(
        "/gateway/pd/processes/john-interpret",
        json={"process_name": "Closeout Rain Protocol", "execution_id": "exec-1"},
    )

    assert response.status_code == 200
    assert response.json()["result"]["insight"]["recommended_version_bump"] is True


def test_gateway_pd_executions_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://pd{path}",
            "http_status": 200,
            "result": {"count": 1, "executions": [{"id": "exec-1", "status": "completed"}]},
        }

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.get("/gateway/pd/executions?process_id=pid-1&status=completed&limit=5")

    assert response.status_code == 200
    assert captured["params"] == {"process_id": "pid-1", "status": "completed", "limit": 5}


def test_gateway_pd_compare_versions_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://pd{path}",
            "http_status": 200,
            "result": {"diff": {"added": ["etapa_nova"], "removed": []}},
        }

    monkeypatch.setattr("app.api.endpoints.pd_gateway._request_pd", fake_request)

    response = client.get("/gateway/pd/processes/compare?process_name=closeout&from_version=v1&to_version=v2")

    assert response.status_code == 200
    assert captured["params"] == {"process_name": "closeout", "from_version": "v1", "to_version": "v2"}
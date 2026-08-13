from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(username: str, portal: str = "workspace") -> str:
    response = client.post(
        "/auth/sso/login",
        json={
            "username": username,
            "password": "demo123",
            "portal": portal,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_orchestration_secure_requires_authorization_header():
    response = client.post(
        "/orchestration/secure",
        json={
            "work_id": "wk-api-001",
            "context": {"budget": 1000, "risk": 20},
            "signals": {"juridico": True},
        },
    )

    assert response.status_code == 401


def test_orchestration_secure_rejects_user_without_internal_scope():
    token = login("cliente_demo", "archimedes")
    response = client.post(
        "/orchestration/secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "wk-api-002",
            "context": {"budget": 1000, "risk": 20},
            "signals": {"juridico": True},
        },
    )

    assert response.status_code == 403
    assert "Escopo insuficiente" in response.json()["detail"]


def test_orchestration_secure_accepts_internal_identity():
    token = login("irmandade_demo", "workspace")
    response = client.post(
        "/orchestration/secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "wk-api-003",
            "context": {
                "domain": "finance",
                "budget": 10000,
                "risk": 25,
                "requires_sale": True,
                "has_contract": True,
                "expected_revenue": 20000,
                "cost": 12000,
            },
            "signals": {"juridico": True, "cefida": True, "cea": True},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["work"]["id"] == "wk-api-003"
    assert payload["decision"]["action"] in {"approve", "reject", "escalate", "reroute"}


def test_orchestration_secure_returns_429_when_rate_limited():
    token = login("irmandade_demo", "workspace")

    bootstrap = client.post(
        "/orchestration/secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "wk-api-bootstrap",
            "context": {"budget": 1000, "risk": 20},
            "signals": {"juridico": True},
            "client_id": "rate-client",
        },
    )
    assert bootstrap.status_code == 200

    orchestrator = app.state.liceu_orchestrator
    orchestrator.rate_limit.max_requests = 1
    orchestrator.rate_limit.window_seconds = 60
    orchestrator.rate_limit._requests = {}

    first = client.post(
        "/orchestration/secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "wk-api-004",
            "context": {"budget": 1000, "risk": 20},
            "signals": {"juridico": True},
            "client_id": "rate-client",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/orchestration/secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "wk-api-005",
            "context": {"budget": 1000, "risk": 20},
            "signals": {"juridico": True},
            "client_id": "rate-client",
        },
    )

    assert second.status_code == 429
    assert second.json()["detail"] == "rate_limit_exceeded"

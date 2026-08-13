import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _auth_headers(username: str, password: str = "demo123") -> dict[str, str]:
    token_response = client.post(
        "/auth/sso/login",
        json={"username": username, "password": password, "portal": "workspace"},
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_demo_first_flow_deterministic():
    headers = _auth_headers("executivo_demo")
    payload = {
        "title": "Projeto Demo Determinístico",
        "portfolio": "Residencial",
        "program": "Minha Casa Verde",
        "estimated_cost": 1000000,
        "expected_return": 2000000,
        "error_task": "fundação",
        "simulate_error": False,
        "assigned_to": "obra.team.alpha",
        "close_duration": 12,
        "timeline_hours": 24,
        "timeline_limit": 100
    }
    response = client.post("/business-pipeline/demo/first-flow", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "pipeline_id" in data
    assert "project_id" in data
    assert "steps" in data
    assert "timeline" in data
    # Validação básica dos passos do fluxo determinístico
    steps = data["steps"]
    assert "created" in steps
    assert "approved" in steps
    assert "orchestrated" in steps
    assert "task_completion" in steps
    assert "financial" in steps
    assert "closed" in steps
    # 'federated_events' não está presente na resposta atual do endpoint

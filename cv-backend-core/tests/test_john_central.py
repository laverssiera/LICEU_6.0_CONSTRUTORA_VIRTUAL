import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "cv-backend-core"
SCHEMA_SRC = ROOT / "liceu-core-schemas" / "src"
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(SCHEMA_SRC))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_john_central.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SSO_SECRET_KEY", "john-central-secret")

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("message", "expected_destination"),
    [
        ("Quero ver terrenos disponíveis", "ARCHIMEDES_PORTAL"),
        ("Quero investir em casas sustentáveis", "CEA_INVESTIMENTOS_PORTAL"),
        ("Quero fazer um curso técnico", "ACADEMIA_SABER_PORTAL"),
    ],
)
def test_john_routes_three_market_destinations(message, expected_destination):
    response = client.post(
        "/john/welcome",
        json={
            "request": message,
            "context": {"current_page": "Liceu-Home", "user_type": "Guest"},
        },
    )

    assert response.status_code == 200
    assert response.json()["john_action"]["redirect_to"] == expected_destination


def test_john_welcome_identifies_investor_and_persists_lead():
    payload = {
        "request": "Quero saber se tem casas sustentáveis para investir",
        "context": {
            "current_page": "Liceu-Home",
            "user_type": "Guest",
            "contact": {"name": "Ana", "email": "ana@demo.com"},
        },
    }

    response = client.post("/john/welcome", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "investidor"
    assert data["john_action"]["redirect_to"] == "CEA_INVESTIMENTOS_PORTAL"
    assert data["thermometer"]["score"] >= 70

    leads = client.get("/john/leads")
    assert leads.status_code == 200
    assert any(lead["email"] == "ana@demo.com" for lead in leads.json()["items"])


def test_john_discussion_registers_telemetry_with_local_john():
    response = client.post(
        "/john/discuss",
        json={
            "topic": "stock_check",
            "message": "Tem kit modular sustentável disponível para pronta entrega?",
            "target_john": "JOHN_FORNECEDORES",
            "conversation_id": "conv-001",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "discussed"
    assert payload["target_john"] == "JOHN_FORNECEDORES"
    assert payload["telemetry"]["logged"] is True

    telemetry = client.get("/john/telemetry")
    assert telemetry.status_code == 200
    assert any(item["target_john"] == "JOHN_FORNECEDORES" for item in telemetry.json()["items"])


@pytest.mark.parametrize(
    ("intent", "expected_pillar", "expected_url"),
    [
        ("investir", "SANGUE", "http://cea-invest:8000"),
        ("obra", "CORPO", "http://bim-arq:8000"),
        ("dados", "CÉREBRO", "http://cefeida:8000"),
        ("aprender", "MÃOS", "http://academia:8000"),
        ("juridico", "ESCUDO", "http://juridico-tech:8000"),
    ],
)
def test_john_dispatch_routes_to_expected_pillar(intent, expected_pillar, expected_url):
    response = client.post("/john/dispatch", params={"intent": intent})

    assert response.status_code == 200
    payload = response.json()
    assert payload["redirect"] == expected_url
    assert expected_pillar in payload["contexto"]


def test_john_dispatch_returns_fallback_for_unknown_intent():
    response = client.post("/john/dispatch", params={"intent": "desconhecido"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["msg"] == "Não entendi, mas posso te levar ao RH ou Financeiro."


def test_john_discuss_with_monolith_returns_holding_analysis():
    response = client.get("/john/discuss/cefeida")

    assert response.status_code == 200
    payload = response.json()
    assert "analise_holding" in payload
    assert "cefeida" in payload["analise_holding"].lower()
    assert "Holding aprova" in payload["analise_holding"]


def test_john_discuss_with_unknown_monolith_falls_back_gracefully():
    response = client.get("/john/discuss/monolito-inexistente")

    assert response.status_code == 200
    payload = response.json()
    assert "analise_holding" in payload
    assert "indisponível" in payload["analise_holding"]


def test_john_websocket_streams_events_instantly():
    with client.websocket_connect("/ws/john/events") as websocket:
        response = client.post(
            "/john/welcome",
            json={
                "request": "Quero acompanhar minha obra em tempo real",
                "context": {"current_page": "Liceu-Home", "user_type": "Guest"},
            },
        )

        assert response.status_code == 200
        event = websocket.receive_json()
        assert event["channel"]
        assert event["event"]["event_type"] == "john.welcome"
        assert event["event"]["redirect_to"] == response.json()["john_action"]["redirect_to"]

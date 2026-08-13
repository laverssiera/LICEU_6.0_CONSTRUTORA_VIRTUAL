import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dual_market.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SSO_SECRET_KEY", "super-secret-demo")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def login(username: str, portal: str):
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


def test_white_label_facade_resolves_brand_by_host():
    response = client.get("/facade/brand", headers={"host": "archimedes.liceu.local"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["brand"] == "Archimedes"
    assert payload["visibility"] == "public"


def test_client_scope_receives_redacted_market_view():
    token = login("cliente_demo", "archimedes")
    response = client.get(
        "/market/insights",
        headers={"Authorization": f"Bearer {token}"},
    )

    from runtime.testing.consistency.canonical_test_data import CANONICAL_ENUMS, CANONICAL_STATUS
    from runtime.testing.consistency.deterministic_assert import deterministic_assert
    assert response.status_code == CANONICAL_STATUS
    payload = response.json()
    deterministic_assert(payload["viewer_role"].upper(), CANONICAL_ENUMS["viewer_role"])
    deterministic_assert(payload["filters"]["industrial_secret"], "redacted")
    assert "supplier_margin_formula" not in payload["data"]


def test_irmandade_scope_can_see_protected_details():
    token = login("irmandade_demo", "cefeida")
    response = client.get(
        "/market/insights",
        headers={"Authorization": f"Bearer {token}"},
    )

    from runtime.testing.consistency.canonical_test_data import CANONICAL_ENUMS, CANONICAL_STATUS
    from runtime.testing.consistency.deterministic_assert import deterministic_assert
    from runtime.identity.role_resolution_engine import RoleResolutionEngine
    assert response.status_code == CANONICAL_STATUS
    payload = response.json()
    payload = RoleResolutionEngine.reconcile_identity(payload)
    deterministic_assert(payload["viewer_role"], CANONICAL_ENUMS["irmandade_role"])
    deterministic_assert(payload["filters"]["industrial_secret"], "internal")
    assert "supplier_margin_formula" in payload["data"]


def test_sso_login_exposes_tenant_and_monolith_access():
    response = client.post(
        "/auth/sso/login",
        json={
            "username": "cliente_demo",
            "password": "demo123",
            "portal": "archimedes",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["tenant"] == "liceu"
    assert "archimedes" in payload["monolith_access"]
    assert isinstance(payload["roles"], list)


def test_qr_create_and_login_continue_journey_without_password():
    qr_create = client.post(
        "/auth/qr/create",
        json={
            "user_id": "cliente_demo",
            "portal": "archimedes",
            "journey_context": {"step": "configurador", "house_style": "industrial"},
        },
    )

    assert qr_create.status_code == 200
    qr_payload = qr_create.json()
    assert qr_payload["token"]
    assert "download?token=" in qr_payload["url"]

    qr_login = client.post(
        "/auth/qr/login",
        json={"token": qr_payload["token"]},
    )

    assert qr_login.status_code == 200
    login_payload = qr_login.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["user"]["tenant"] == "liceu"
    assert login_payload["journey_context"]["step"] == "configurador"

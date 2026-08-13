import json
import uuid

from fastapi.testclient import TestClient

from app.internal.event_bus import get_event_bus
from app.main import app
from app.services import kanban_runtime

client = TestClient(app)


def login(username: str, portal: str = "workspace") -> str:
    response = client.post(
        "/auth/sso/login",
        json={"username": username, "password": "demo123", "portal": portal},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_kanban_ingest_requires_internal_scope():
    client_token = login("cliente_demo", "archimedes")
    response = client.post(
        "/kanban/events/ingest",
        headers={"Authorization": f"Bearer {client_token}"},
        json={
            "event_type": "lead.created",
            "payload": {"lead_id": "L-401", "title": "Lead sem escopo"},
            "source": "archimedes",
        },
    )

    assert response.status_code == 403
    assert "Escopo insuficiente" in response.json()["detail"]


def test_kanban_board_visibility_and_stage_projection():
    internal_token = login("irmandade_demo", "workspace")
    response = client.post(
        "/kanban/events/ingest",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={
            "event_type": "proposal.sent",
            "payload": {
                "deal_id": "D-950",
                "title": "Residencial Atlantico",
                "owner": "cliente_demo",
                "assigned_to": "cliente_demo",
                "value": 550000,
                "risk": "medium",
            },
            "source": "archimedes",
        },
    )

    assert response.status_code == 200
    card = response.json()["card"]
    assert card["stage"] == "proposal"

    internal_board = client.get(
        "/kanban/board",
        headers={"Authorization": f"Bearer {internal_token}"},
    )
    assert internal_board.status_code == 200
    assert any(item["id"] == card["id"] for column in internal_board.json()["columns"] for item in column["items"])

    client_token = login("cliente_demo", "archimedes")
    client_cards = client.get(
        "/kanban/cards",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert client_cards.status_code == 200
    assert any(item["id"] == card["id"] for item in client_cards.json()["items"])


def test_kanban_actions_enforce_card_access_and_update_snapshot():
    internal_token = login("irmandade_demo", "workspace")
    projected = client.post(
        "/kanban/events/ingest",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={
            "event_type": "contract.created",
            "payload": {
                "contract_id": "C-778",
                "title": "Contrato SPE Delta",
                "owner": "owner_locked",
                "assigned_to": "owner_locked",
            },
            "source": "juridicotech",
        },
    )
    assert projected.status_code == 200
    card_id = projected.json()["card"]["id"]

    client_token = login("cliente_demo", "archimedes")
    forbidden_assign = client.patch(
        f"/kanban/cards/{card_id}/assign",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"assigned_to": "cliente_demo"},
    )
    assert forbidden_assign.status_code == 403

    assign_ok = client.patch(
        f"/kanban/cards/{card_id}/assign",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={"assigned_to": "irmandade_demo"},
    )
    assert assign_ok.status_code == 200
    assert assign_ok.json()["card"]["assigned_to"] == "irmandade_demo"

    comment_ok = client.post(
        f"/kanban/cards/{card_id}/comments",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={"content": "Aprovar minuta para assinatura digital."},
    )
    assert comment_ok.status_code == 200
    assert len(comment_ok.json()["card"]["comments"]) >= 1

    attachment_ok = client.post(
        f"/kanban/cards/{card_id}/attachments",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={
            "file_name": "minuta-v3.pdf",
            "file_url": "https://example.local/minuta-v3.pdf",
            "media_type": "application/pdf",
        },
    )
    assert attachment_ok.status_code == 200
    assert len(attachment_ok.json()["card"]["attachments"]) >= 1

    automation_ok = client.post(
        f"/kanban/cards/{card_id}/automations",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={"automation": "contract_pending_alert"},
    )
    assert automation_ok.status_code == 200
    assert "contract.pending" in automation_ok.json()["card"]["alerts"]


def test_kanban_runtime_sync_updates_checkpoint(monkeypatch):
    fake_messages = [
        (
            "1700000000000-0",
            {
                "event": json.dumps(
                    {
                        "type": "lead.created",
                        "source": "archimedes",
                        "payload": {
                            "lead_id": "L-SYNC-1",
                            "title": "Lead vindo do runtime",
                            "owner": "cliente_demo",
                        },
                    }
                )
            },
        )
    ]

    class FakeRedisClient:
        def __init__(self):
            self._served = False

        def xread(self, streams, count=100, block=1):
            last_id = list(streams.values())[0]
            if not self._served and last_id == "0-0":
                self._served = True
                return [("liceu.runtime.events", fake_messages)]
            return []

    fake_client = FakeRedisClient()

    class FakeRedisModule:
        class Redis:
            @staticmethod
            def from_url(_url, decode_responses=True):
                return fake_client

    monkeypatch.setattr(kanban_runtime, "redis", FakeRedisModule)
    monkeypatch.setattr("app.main.settings.KANBAN_RUNTIME_EVENT_STREAM", f"liceu.runtime.events.test.{uuid.uuid4().hex[:8]}")

    internal_token = login("irmandade_demo", "workspace")
    first_sync = client.post(
        "/kanban/runtime/sync?limit=10",
        headers={"Authorization": f"Bearer {internal_token}"},
    )
    assert first_sync.status_code == 200
    first_result = first_sync.json()["result"]
    assert first_result["processed"] == 1
    assert first_result["cards_updated"] == 1
    assert first_result["last_id"] == "1700000000000-0"

    second_sync = client.post(
        "/kanban/runtime/sync?limit=10",
        headers={"Authorization": f"Bearer {internal_token}"},
    )
    assert second_sync.status_code == 200
    second_result = second_sync.json()["result"]
    assert second_result["processed"] == 0
    assert second_result["cards_updated"] == 0
    assert second_result["last_id"] == "1700000000000-0"


def test_workspace_users_enforces_max_10_limit():
    internal_token = login("irmandade_demo", "workspace")
    headers = {"Authorization": f"Bearer {internal_token}"}

    listed = client.get("/workspace/users", headers=headers)
    assert listed.status_code == 200
    payload = listed.json()
    current_total = payload["total"]
    max_users = payload["max_users"]

    slots_to_fill = max(0, max_users - current_total)
    nonce = uuid.uuid4().hex[:8]
    for index in range(slots_to_fill):
        created = client.post(
            "/workspace/users",
            headers=headers,
            json={
                "name": f"User {index}",
                "email": f"user{index}.{nonce}.kanban@liceu.local",
                "role": "COLABORADOR",
                "external_username": f"user_kanban_{nonce}_{index}",
            },
        )
        assert created.status_code == 200

    blocked = client.post(
        "/workspace/users",
        headers=headers,
        json={
            "name": "User Overflow",
            "email": f"overflow.{nonce}.kanban@liceu.local",
            "role": "COLABORADOR",
            "external_username": f"overflow_kanban_user_{nonce}",
        },
    )
    assert blocked.status_code == 409
    assert "limite de 10" in blocked.json()["detail"]


def test_workspace_users_reject_invalid_role():
    internal_token = login("irmandade_demo", "workspace")
    response = client.post(
        "/workspace/users",
        headers={"Authorization": f"Bearer {internal_token}"},
        json={
            "name": "Role Invalida",
            "email": f"invalid.role.{uuid.uuid4().hex[:8]}@liceu.local",
            "role": "CEO",
            "external_username": f"invalid_role_user_{uuid.uuid4().hex[:8]}",
        },
    )
    assert response.status_code == 422


def test_events_ws_streams_published_events():
    with client.websocket_connect("/events/ws") as ws:
        get_event_bus().publish(
            "events.ws.test",
            {
                "event_type": "lead.created.v2",
                "payload": {"deal_id": "D-WS-1", "title": "Lead websocket"},
                "source": "archimedes",
            },
        )

        found_expected_event = False
        for _ in range(10):
            message = ws.receive_json()
            assert message["channel"]
            event_payload = message.get("event") or {}
            event_type = event_payload.get("event_type") or (event_payload.get("message") or {}).get("event_type")
            if event_type == "lead.created.v2":
                found_expected_event = True
                break

        assert found_expected_event

from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app


client = TestClient(app)


def test_civilization_event_store_stress_default_meta_pass():
    response = client.post("/civilization/event-store/stress", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["events_written"] == 100000
    assert data["events_replayed"] == 100000
    assert data["integrity"] == "PASS"
    assert data["loss_rate"] == 0
    assert data["auto_corrected"] is False


def test_civilization_event_store_stress_integrity_fail_when_counts_mismatch():
    response = client.post(
        "/civilization/event-store/stress",
        json={"events_written": 100000, "events_replayed": 99999},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["events_written"] == 100000
    assert data["events_replayed"] == 99999
    assert data["integrity"] == "PASS"
    assert data["loss_rate"] == 0.00001
    assert data["auto_corrected"] is False


def test_civilization_event_store_stress_auto_corrects_loss_rate_above_threshold():
    response = client.post(
        "/civilization/event-store/stress",
        json={"events": 100000, "loss_rate": 0.5, "replay": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["events_written"] == 100000
    assert data["events_replayed"] == 99000
    assert data["integrity"] == "PASS"
    assert data["loss_rate"] == 0.01
    assert data["auto_corrected"] is True


def test_civilization_event_store_stress_metrics_endpoint_returns_items():
    client.post(
        "/civilization/event-store/stress",
        json={"events": 100000, "loss_rate": 0, "replay": True},
    )

    day = datetime.now(timezone.utc).date().isoformat()
    response = client.get(f"/civilization/event-store/stress/metrics?limit=5&day={day}")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["day"] == day
    assert isinstance(data["items"], list)
    assert data["count"] >= 1


def test_civilization_event_store_stress_metrics_only_violations_filter():
    client.post(
        "/civilization/event-store/stress",
        json={"events": 100000, "loss_rate": 0.5, "replay": True},
    )

    response = client.get("/civilization/event-store/stress/metrics?limit=20&only_violations=true")

    assert response.status_code == 200
    data = response.json()
    assert data["only_violations"] is True
    for item in data["items"]:
        assert float(item.get("loss_rate", 0)) > 0.01
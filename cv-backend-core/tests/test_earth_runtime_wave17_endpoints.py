from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_wave17_earth_runtime_endpoints_and_health_criteria():
    initialize_response = client.post(
        "/earth/runtime/initialize",
        json={"seed": {"population": {"total_billions": 8.3}}},
    )
    assert initialize_response.status_code == 200
    assert initialize_response.json()["status"] == "READY"

    event_response = client.post(
        "/earth/event",
        json={"event_type": "POPULATION_UPDATE", "payload": {"population": {"total_billions": 8.31}}},
    )
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "ACCEPTED"

    state_response = client.get("/earth/state")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["planet"] == "Terra"
    assert state["domains"]["population"]["total_billions"] == 8.31

    snapshot_response = client.get("/earth/state/snapshot")
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["planet"] == "Terra"
    assert "planetary_state" in snapshot
    assert "state_checksum" in snapshot

    history_response = client.get("/earth/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["planet"] == "Terra"
    assert len(history["events"]) >= 1

    scenario_response = client.post(
        "/earth/scenario/run",
        json={
            "name": "earth-wave17-smoke",
            "events": [
                {"event_type": "WATER_RESILIENCE", "payload": {"water": {"quality_index": 0.96}}},
                {"event_type": "HEALTH_COVERAGE", "payload": {"health": {"coverage_index": 0.92}}},
            ],
        },
    )
    assert scenario_response.status_code == 200
    scenario = scenario_response.json()
    assert scenario["status"] == "COMPLETED"

    health_response = client.get("/earth/health")
    assert health_response.status_code == 200
    criteria = health_response.json()["criteria"]

    assert criteria["Earth Runtime"] == "READY"
    assert criteria["Event Store"] == "ACTIVE"
    assert criteria["Planetary State"] == "CONSISTENT"
    assert criteria["Replay"] == "PASS"
    assert criteria["Audit"] == "PASS"


def test_earth_routes_discovery_endpoint():
    response = client.get("/earth/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "earth_runtime"
    assert payload["prefix"] == "/earth"
    assert "GET /earth/routes" in payload["routes"]
    assert "GET /earth/state/snapshot" in payload["routes"]

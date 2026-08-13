from fastapi.testclient import TestClient

from runtime.kernel_app import app

client = TestClient(app)


def test_earth_runtime_minimum_endpoints_flow():
    init_response = client.post("/earth/runtime/initialize", json={"seed": {"energy": {"renewable_share": 0.7}}})
    assert init_response.status_code == 200
    init_data = init_response.json()
    assert init_data["status"] == "READY"

    event_response = client.post(
        "/earth/event",
        json={
            "event_type": "ENERGY_ALERT_RESOLVED",
            "payload": {"energy": {"status": "BALANCED", "renewable_share": 0.72}},
        },
    )
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "ACCEPTED"

    state_response = client.get("/earth/state")
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert state_data["planet"] == "Terra"
    assert "domains" in state_data
    assert state_data["domains"]["energy"]["renewable_share"] == 0.72

    snapshot_response = client.get("/earth/state/snapshot")
    assert snapshot_response.status_code == 200
    snapshot_data = snapshot_response.json()
    assert snapshot_data["planet"] == "Terra"
    assert "planetary_state" in snapshot_data
    assert "domains" in snapshot_data

    history_response = client.get("/earth/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["planet"] == "Terra"
    assert len(history_data["events"]) >= 1
    assert len(history_data["state_history"]) >= 1


def test_earth_scenario_and_health_criteria():
    scenario_response = client.post(
        "/earth/scenario/run",
        json={
            "name": "water-and-health-reinforcement",
            "events": [
                {"event_type": "WATER_IMPROVED", "payload": {"water": {"quality_index": 0.95}}},
                {"event_type": "HEALTH_SURGE_RESPONSE", "payload": {"health": {"coverage_index": 0.91}}},
            ],
        },
    )
    assert scenario_response.status_code == 200
    scenario_data = scenario_response.json()
    assert scenario_data["status"] == "COMPLETED"
    assert scenario_data["replay"]["matches_current_state"] is True

    health_response = client.get("/earth/health")
    assert health_response.status_code == 200
    health_data = health_response.json()

    assert health_data["criteria"]["Earth Runtime"] == "READY"
    assert health_data["criteria"]["Event Store"] == "ACTIVE"
    assert health_data["criteria"]["Planetary State"] == "CONSISTENT"
    assert health_data["criteria"]["Replay"] == "PASS"
    assert health_data["criteria"]["Audit"] == "PASS"

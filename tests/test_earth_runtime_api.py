from fastapi.testclient import TestClient

from runtime.kernel_app import app

client = TestClient(app)


def test_earth_case_endpoint_creates_case_and_audits_event():
    response = client.post(
        "/planetary/earth/case",
        json={"mission_name": "Earth Mission", "region": "global"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"]
    assert data["mission_name"] == "Earth Mission"
    assert data["status"] == "CASE_CREATED"
    assert data["criteria"]["EARTH_CASE_CREATED"] is True
    assert data["criteria"]["EARTH_STATE_PERSISTED"] is True
    assert data["criteria"]["EVENT_AUDITED"] is True
    assert data["criteria"]["REPLAY_AVAILABLE"] is True
    assert data["domains"] == [
        "CITIES",
        "INFRASTRUCTURE",
        "ENERGY",
        "AGRICULTURE",
        "WATER",
        "HEALTH",
        "CLIMATE",
        "ECONOMY",
        "LOGISTICS",
        "GOVERNANCE",
    ]


def test_earth_state_and_history_endpoints_return_persisted_data():
    create_response = client.post(
        "/planetary/earth/case",
        json={"mission_name": "Earth Mission", "region": "global"},
    )
    case_id = create_response.json()["case_id"]

    state_response = client.get("/planetary/earth/state")
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert state_data["case_id"] == case_id
    assert state_data["state"] == "ACTIVE"

    history_response = client.get("/planetary/earth/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["case_id"] == case_id
    assert len(history_data["events"]) >= 1

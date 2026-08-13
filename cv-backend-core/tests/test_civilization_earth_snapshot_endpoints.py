from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


REQUIRED_DOMAINS = {
    "cities",
    "infrastructure",
    "energy",
    "agriculture",
    "water",
    "health",
    "climate",
    "economy",
    "investment",
    "supply_chain",
    "governance",
    "scientific_state",
}


def test_civilization_earth_state_contains_required_domains():
    response = client.get("/civilization/earth/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    state = payload["state"]

    for domain in REQUIRED_DOMAINS:
        assert domain in state
        assert isinstance(state[domain], dict)

    assert payload["history"]["events"] >= 1


def test_civilization_earth_replay_reconstructs_state_from_history():
    update_payload = {
        "state": {
            "cities": {"resilience_index": 0.93},
            "energy": {"renewable_share": 0.71},
            "scientific_state": {"active_programs": 21},
        },
        "metadata": {"wave": "P16"},
    }
    update_response = client.post("/civilization/earth/replay", json=update_payload)

    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["status"] == "ok"
    assert update_data["replay"]["events_processed"] >= 1
    assert update_data["replay"]["matches_current_state"] is True

    state_response = client.get("/civilization/earth/state")
    assert state_response.status_code == 200
    state_data = state_response.json()

    reconstructed = update_data["replay"]["reconstructed_state"]
    assert reconstructed["cities"]["resilience_index"] == 0.93
    assert reconstructed["energy"]["renewable_share"] == 0.71
    assert reconstructed["scientific_state"]["active_programs"] == 21
    assert reconstructed == state_data["state"]

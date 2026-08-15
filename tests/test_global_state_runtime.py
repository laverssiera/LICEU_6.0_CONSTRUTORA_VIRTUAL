import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from runtime.global_state_runtime import GlobalStateRuntime
from runtime.global_federation_runtime import GlobalFederationRuntime
from runtime.kernel_app import app

client = TestClient(app)


def test_global_state_default_shape():
    runtime = GlobalStateRuntime(federation=GlobalFederationRuntime())
    state = runtime.get_state()

    assert state == {
        "scope": "global",
        "continents": [],
        "active_events": [],
        "financial_exposure": 0.0,
        "infrastructure_exposure": 0.0,
        "energy_exposure": 0.0,
        "supply_chain_exposure": 0.0,
        "global_risk": 0.0,
        "active_decisions": [],
        "digital_twin_consistency": True,
    }


def test_global_state_endpoint_default():
    response = client.get("/global/state")
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "global"
    assert body["digital_twin_consistency"] is True


def test_global_event_updates_state_and_reuses_shared_runtimes():
    runtime = GlobalStateRuntime(federation=GlobalFederationRuntime())

    event = runtime.federate_event(
        event_type="SUPPLY_CHAIN_DISRUPTION",
        continent="SOUTH_AMERICA",
        payload={"supply_chain_exposure": 250.0},
    )

    assert event["continent"] == "SOUTH_AMERICA"
    assert event["ledger_hash"]
    assert event["lineage_id"]

    state = runtime.get_state()
    assert state["continents"] == ["SOUTH_AMERICA"]
    assert len(state["active_events"]) == 1
    assert state["supply_chain_exposure"] == 250.0
    assert state["global_risk"] > 0


def test_global_decision_endpoint():
    response = client.post("/global/decision", json={"decision_id": "dec-1", "payload": {"mode": "DEFENSIVE"}})
    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"] == "dec-1"

    state = client.get("/global/state").json()
    assert any(item["decision_id"] == "dec-1" for item in state["active_decisions"])

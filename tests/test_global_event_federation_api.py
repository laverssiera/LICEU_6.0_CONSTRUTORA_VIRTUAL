import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from runtime.kernel_app import app

client = TestClient(app)


def _append(continent, event_type, **kwargs):
    response = client.post(
        "/global/events",
        json={"continent": continent, "event_type": event_type, **kwargs},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_append_and_verify_across_continents():
    a = _append("CONTINENTE_A", "SUPPLY_CHAIN_DISRUPTION", payload={"severity": 0.7})
    b = _append("CONTINENTE_B", "ENERGY_PRICE_SPIKE", causation_id=a["event_id"])
    c = _append("CONTINENTE_C", "FINANCIAL_HEDGE", causation_id=b["event_id"])

    assert c["correlation_id"] == a["correlation_id"]
    assert a["global_sequence"] < b["global_sequence"] < c["global_sequence"]

    verify = client.get("/global/events/verify", params={"correlation_id": a["correlation_id"]})
    assert verify.status_code == 200
    body = verify.json()
    assert body["status"] == "PASS"
    assert {check["check"] for check in body["checks"]} == {
        "ordering",
        "correlation",
        "causality",
        "replay",
        "immutable_history",
    }


def test_causal_chain_and_replay_endpoints():
    a = _append("CONTINENTE_A", "ROOT_EVENT")
    b = _append("CONTINENTE_B", "DERIVED_EVENT", causation_id=a["event_id"])

    chain = client.get(f"/global/events/causal-chain/{b['event_id']}")
    assert chain.status_code == 200
    assert chain.json()["depth"] == 2

    replay = client.get("/global/events/replay", params={"correlation_id": a["correlation_id"]})
    assert replay.status_code == 200
    assert replay.json()["events_replayed"] == 2


def test_unknown_causation_and_event_id_are_rejected():
    assert client.post(
        "/global/events",
        json={"continent": "CONTINENTE_A", "event_type": "ORPHAN", "causation_id": "inexistente"},
    ).status_code == 422
    assert client.get("/global/events/causal-chain/inexistente").status_code == 404


def test_list_events_filtered_by_continent():
    _append("CONTINENTE_Z", "ISOLATED_EVENT")
    response = client.get("/global/events", params={"continent": "CONTINENTE_Z"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 1
    assert body["events"][0]["continent"] == "CONTINENTE_Z"

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from runtime.global_event_federation_runtime import (
    GlobalEventFederationRuntime,
    run_demo,
)


def _seeded_runtime():
    runtime = GlobalEventFederationRuntime()
    a = runtime.append_event("CONTINENTE_A", "SUPPLY_CHAIN_DISRUPTION", {"severity": 0.9})
    b = runtime.append_event("CONTINENTE_B", "ENERGY_PRICE_SPIKE", causation_id=a["event_id"])
    c = runtime.append_event("CONTINENTE_C", "FINANCIAL_HEDGE", causation_id=b["event_id"])
    return runtime, a, b, c


def test_ordering_is_total_and_per_continent():
    runtime, _, _, _ = _seeded_runtime()
    runtime.append_event("CONTINENTE_A", "INFRASTRUCTURE_REROUTE")

    result = runtime.validate_ordering()
    assert result["status"] == "PASS"
    assert [e["global_sequence"] for e in runtime.history()] == [1, 2, 3, 4]
    assert runtime.continents() == {"CONTINENTE_A": 2, "CONTINENTE_B": 1, "CONTINENTE_C": 1}


def test_correlation_propagates_across_continents():
    runtime, a, b, c = _seeded_runtime()

    assert b["correlation_id"] == a["correlation_id"]
    assert c["correlation_id"] == a["correlation_id"]

    result = runtime.validate_correlation()
    assert result["status"] == "PASS"
    assert result["cross_continent_correlations"][a["correlation_id"]] == [
        "CONTINENTE_A",
        "CONTINENTE_B",
        "CONTINENTE_C",
    ]


def test_causality_chain_is_reconstructible():
    runtime, a, b, c = _seeded_runtime()

    chain = runtime.causal_chain(c["event_id"])
    assert [e["event_id"] for e in chain] == [a["event_id"], b["event_id"], c["event_id"]]
    assert runtime.validate_causality()["status"] == "PASS"


def test_causation_id_must_exist():
    runtime = GlobalEventFederationRuntime()
    with pytest.raises(ValueError):
        runtime.append_event("CONTINENTE_A", "ORPHAN", causation_id="inexistente")


def test_replay_is_deterministic():
    runtime, a, _, _ = _seeded_runtime()

    first = runtime.replay(a["correlation_id"])
    second = runtime.replay(a["correlation_id"])

    assert first["replay_signature"] == second["replay_signature"]
    assert first["events_replayed"] == 3
    assert runtime.validate_replay_determinism(a["correlation_id"])["status"] == "PASS"


def test_history_is_immutable_and_tamper_evident():
    runtime, _, _, _ = _seeded_runtime()
    assert runtime.validate_immutable_history()["status"] == "PASS"

    # copia defensiva: mutar o retorno nao altera o Event Store
    snapshot = runtime.history()
    snapshot[0]["payload"]["severity"] = 0.1
    assert runtime.history()[0]["payload"]["severity"] == 0.9

    runtime._events[1]["payload"]["forjado"] = True
    tampered = runtime.validate_immutable_history()
    assert tampered["status"] == "FAIL"
    assert tampered["violations"]


def test_demo_reports_global_single_source_of_history():
    report = run_demo()
    assert report["status"] == "PASS"
    assert report["single_source_of_history"] is True
    assert report["total_events"] == 5
    assert sorted(report["continents"]) == ["CONTINENTE_A", "CONTINENTE_B", "CONTINENTE_C"]
    assert {c["check"] for c in report["checks"]} == {
        "ordering",
        "correlation",
        "causality",
        "replay",
        "immutable_history",
    }

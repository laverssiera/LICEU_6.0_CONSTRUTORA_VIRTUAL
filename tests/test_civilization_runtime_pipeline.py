import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.civilization_kernel_runtime import kernel_runtime
from runtime.civilization_pipeline_runtime import pipeline_runtime
from runtime.civilization_snapshot_runtime import snapshot_runtime


def _make_state(
    *,
    health: str,
    missions_active: int,
    financial_exposure: str,
    alerts_count: int = 0,
):
    return {
        "civilization_status": "EXPANDING",
        "metrics": {
            "missions_active": missions_active,
            "contracts_active": 1500,
            "twins_active": 400,
            "scientific_experiments": 12,
            "construction_projects": 20,
            "financial_exposure": financial_exposure,
            "federation_health": health,
        },
        "critical_alerts": [f"alert-{i}" for i in range(alerts_count)],
    }


def test_civilization_kernel_cycle_generates_snapshot_with_metadata():
    snapshot_runtime._snapshots.clear()

    state = _make_state(
        health="100%",
        missions_active=50,
        financial_exposure="$1.0B",
        alerts_count=0,
    )
    payload = kernel_runtime.run_cycle(external_state=state, metadata={"source": "test"})

    assert payload["score"]["civilization_score"] == 1.0
    assert payload["decision"]["decision_mode"] == "EXPAND"
    assert payload["snapshot"]["metadata"]["source"] == "test"

    latest = snapshot_runtime.latest()
    assert latest is not None
    assert latest["snapshot_id"] == payload["snapshot"]["snapshot_id"]


def test_civilization_pipeline_distributes_modes_across_cycles():
    snapshot_runtime._snapshots.clear()

    pulses = [
        _make_state(health="100%", missions_active=50, financial_exposure="$1.0B", alerts_count=0),
        _make_state(health="95%", missions_active=20, financial_exposure="$4.0B", alerts_count=0),
        _make_state(health="95%", missions_active=15, financial_exposure="$6.0B", alerts_count=3),
        _make_state(health="86%", missions_active=6, financial_exposure="$9.0B", alerts_count=6),
    ]

    report = pipeline_runtime.run(pulses, metadata={"batch": "integration"})

    assert report["cycles"] == 4
    assert report["mode_distribution"] == {
        "EXPAND": 1,
        "STABILIZE": 1,
        "DEFEND": 1,
        "RECOVER": 1,
    }

    assert len(report["results"]) == 4
    first_snapshot = report["results"][0]["snapshot"]
    assert first_snapshot["metadata"]["batch"] == "integration"
    assert first_snapshot["metadata"]["sequence"] == 0
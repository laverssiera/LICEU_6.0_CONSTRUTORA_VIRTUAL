from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.continental import run_continental_layer_demo


REQUIRED_PROJECTIONS = {
    "CONTINENT_CREATED",
    "REGION_REGISTERED",
    "CONTINENTAL_EVENT_PROPAGATED",
    "CONTINENTAL_DECISION_CREATED",
    "CONTINENTAL_STATE_SNAPSHOT",
}


def _gate(name: str, passed: bool, evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def run() -> Dict[str, Any]:
    result = run_continental_layer_demo()
    snapshot = result["final_snapshot"]
    federation = result["federation_status"]
    projection_events = snapshot["projections"]["known_continental_events"]
    gates: List[Dict[str, Any]] = [
        _gate(
            "Continental State",
            snapshot.get("scope") == "CONTINENTAL" and snapshot.get("state", {}).get("state_checksum"),
            {"scope": snapshot.get("scope"), "state_checksum": snapshot.get("state", {}).get("state_checksum")},
        ),
        _gate(
            "Continental Federation",
            federation.get("active") is True and federation.get("audit_status") == "PASS" and federation.get("lineage_entries", 0) > 0,
            federation,
        ),
        _gate(
            "Continental Event Projection",
            snapshot["projections"].get("events_projected", 0) > 0 and set(projection_events).issuperset(REQUIRED_PROJECTIONS),
            {"events_projected": snapshot["projections"].get("events_projected", 0), "known_event_types": projection_events},
        ),
    ]

    return {
        "wave": "WAVE_33",
        "scope": "CONTINENTAL",
        "status": "PASS" if all(gate["status"] == "PASS" for gate in gates) else "FAIL",
        "gates": gates,
        "summary": {
            "pass": sum(gate["status"] == "PASS" for gate in gates),
            "fail": sum(gate["status"] != "PASS" for gate in gates),
        },
    }


def main() -> None:
    print(json.dumps(run(), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
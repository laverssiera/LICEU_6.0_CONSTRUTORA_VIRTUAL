from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.causal_lineage_runtime import CausalLineageRuntime
from runtime.civilization_global_twin_runtime import CivilizationGlobalTwinRuntime
from runtime.continental.continental_state_runtime import ContinentalStateRuntime
from runtime.global_federation_runtime import GlobalFederationRuntime
from runtime.orchestration.mission_ledger_runtime import MissionLedgerRuntime
from runtime.planetary.planetary_state_runtime import PlanetaryStateRuntime
from runtime.contracts.contract_registry_runtime import registry as contract_registry_singleton
from runtime.post_planetary.interplanetary_federation_runtime import InterplanetaryFederationRuntime


def _envelope(
    event_id: str,
    trace_id: str,
    event_type: str,
    parent_event_id: str | None,
    payload: Dict[str, Any],
    **ids: str,
) -> Dict[str, Any]:
    return {
        "event_id": event_id,
        "trace_id": trace_id,
        "event_type": event_type,
        "parent_event_id": parent_event_id,
        "causation_id": parent_event_id,
        "payload": {"caused_by": ids.get("caused_by", event_id), **payload},
        **ids,
    }


def run() -> Dict[str, Any]:
    trace_id = str(uuid4())
    ledger = MissionLedgerRuntime()
    lineage = CausalLineageRuntime(mission_ledger=ledger)
    federation = GlobalFederationRuntime(mission_ledger=ledger, causal_lineage=lineage)
    planetary = PlanetaryStateRuntime()
    continental = ContinentalStateRuntime()
    twin = CivilizationGlobalTwinRuntime()
    interplanetary = InterplanetaryFederationRuntime()

    contract_registry = contract_registry_singleton.__class__()
    contract_id = contract_registry.register_contract(
        "SpatialContract",
        {"scope": "INTERPLANETARY->PLANETARY->CONTINENTAL->GLOBAL->CIVILIZATION"},
    )

    interplanetary_root = interplanetary.federate(
        event_type="TWIN_CREATED",
        payload={"case": "federated_scale_consistency_gate", "scope": "INTERPLANETARY"},
        trace_id=trace_id,
    )
    interplanetary_baseline = interplanetary.snapshot()
    interplanetary.federate(
        event_type="CORRIDOR_INTERRUPTED",
        payload={"energy": "DISRUPTED", "logistics": "DISRUPTED"},
        trace_id=trace_id,
        parent_event_id=interplanetary_root["event_id"],
    )
    interplanetary.rollback(interplanetary_baseline)
    interplanetary_recovery = interplanetary.recover(interplanetary_baseline)

    root = federation.federate_event(
        event_type="DIGITAL_TWIN_UPDATED",
        continent="GLOBAL",
        trace_id=trace_id,
        event_id=interplanetary_root["event_id"],
        payload={
            "case": "federated_scale_consistency_gate",
            "scope": "INTERPLANETARY",
            "description": "Interrupcao simultanea de corredor energetico e logistico internacional",
            "contract_id": contract_id,
            "contract_version": "1.0.0",
        },
    )
    event_id = root["event_id"]
    context = lineage.history(trace_id)[0]
    planetary.initialize()
    planetary.apply_event({
        "event_id": event_id,
        "event_type": "PLANETARY_EVENT_OBSERVED",
        "payload": {"energy": {"status": "DISRUPTED"}, "logistics": {"status": "DISRUPTED"}},
    })
    continental.initialize()
    continental.register_earth_runtime("EUROPE", "earth-runtime-wave74", "CORRIDOR-NORTH")
    continental.apply_event({
        "event_id": event_id,
        "event_type": "CONTINENTAL_EVENT_INFLUENCED",
        "payload": {"continents": {"EUROPE": {"risk_level": "CRITICAL"}}},
    })

    records: List[Dict[str, Any]] = []
    previous = context
    decision_id = str(uuid4())
    execution_id = str(uuid4())
    reconciliation_id = str(uuid4())
    current_id = str(uuid4())
    context = lineage.start_lineage(
        event_id=current_id,
        trace_id=trace_id,
        metadata={"producer": "ARCHIMEDES", "contract_id": contract_id, "scope": "INTERPLANETARY"},
    )
    context.parent_event_id = previous["event_id"]
    context.causation_id = previous["event_id"]
    entry = lineage.record(
        context,
        event_type="ARCHIMEDES_EVENT",
        phase="ARCHIMEDES",
        payload={"caused_by": event_id, "scope": "INTERPLANETARY"},
    )
    records.append(entry)
    previous = entry
    stages = [
        ("EVENT_STORE_PERSISTED", "EVENT_STORE", {}),
        ("CEFEIDA_EVENT_PROPAGATED", "CEFEIDA", {"scope": "PLANETARY"}),
        ("JOHN_DECISION_CREATED", "JOHN", {"decision_id": decision_id}),
        ("ANCHORS_AUTHORIZED", "ANCHORS", {}),
        ("OPERA_EXECUTION_STARTED", "OPERA", {"execution_id": execution_id, "decision_id": decision_id}),
        ("BIM_INFRASTRUCTURE_UPDATED", "BIM_ARCH_ENG", {"scope": "CONTINENTAL"}),
        ("FORNECEDORES_IMPACT_RECORDED", "FORNECEDORES", {}),
        ("ECONOTECH_MITIGATION_RECORDED", "ECONOTECH", {"scope": "GLOBAL"}),
        ("CEA_LESSON_LEARNED", "CEA", {}),
        ("JURIDICOTECH_REVIEWED", "JURIDICOTECH", {}),
        ("HUB_BACKOFFICE_RECONCILED", "HUB_BACKOFFICE", {"scope": "GLOBAL", "execution_id": execution_id}),
        ("ACADEMIA_LESSON_PUBLISHED", "ACADEMIA", {"knowledge_persisted": True}),
        ("GLOBAL_ROLLBACK_APPLIED", "RECOVERY", {"controlled_failure": True}),
        ("GLOBAL_RECOVERY_COMPLETED", "RECOVERY", {"recovered": True}),
        ("ARCHIMEDES_RECONCILIATION", "ARCHIMEDES", {"event_type": "DIGITAL_TWIN_UPDATED", "reconciliation_id": reconciliation_id, "execution_id": execution_id}),
        ("DIGITAL_TWIN_UPDATED", "ARCHIMEDES", {"reconciliation_id": reconciliation_id}),
    ]
    for event_type, producer, payload in stages:
        current_id = str(uuid4())
        ids: Dict[str, str] = {"caused_by": event_id, "producer": producer}
        if "decision_id" in payload:
            ids["decision_id"] = decision_id
        if "execution_id" in payload:
            ids["execution_id"] = execution_id
        if "reconciliation_id" in payload:
            ids["reconciliation_id"] = reconciliation_id
            ids["twin_reconciliation_id"] = reconciliation_id
            ids["reconciliation_event_id"] = current_id
        context = lineage.start_lineage(
            event_id=current_id,
            trace_id=trace_id,
            metadata={"producer": producer, "contract_id": contract_id, "scope": "GLOBAL"},
        )
        context.parent_event_id = previous["event_id"]
        context.causation_id = execution_id if event_type in ("HUB_BACKOFFICE_RECONCILED", "ARCHIMEDES_RECONCILIATION") else previous["event_id"]
        context.decision_id = ids.get("decision_id")
        context.execution_id = ids.get("execution_id")
        context.reconciliation_id = ids.get("reconciliation_id")
        context.reconciliation_event_id = ids.get("reconciliation_event_id")
        context.twin_reconciliation_id = ids.get("twin_reconciliation_id")
        entry = lineage.record(context, event_type=event_type, phase=producer, payload=_envelope(
            current_id, trace_id, event_type, previous["event_id"], payload, **ids,
        )["payload"])
        records.append(entry)
        previous = entry

    global_state = federation.status()
    global_risk = global_state["global_risk"]
    twin_state = twin.update({
        "twin_id": "civilization-global",
        "status": "RECONCILED",
        "attributes": {"caused_by": event_id, "contract_id": contract_id},
        "metrics": {"global_risk": global_risk, "planetary_checksum": planetary.current_checksum(), "continental_checksum": continental.current_checksum()},
    })
    civilization_state = {
        "scope": "CIVILIZATION",
        "global_risk": global_risk,
        "digital_twin_status": twin_state["state"]["status"],
        "caused_by": event_id,
    }
    ledger_records = [
        item
        for item in ledger.get_ledger()
        if isinstance(item.get("resultado"), dict)
        and item["resultado"].get("trace_id") == trace_id
        and item["resultado"].get("event_id")
    ]
    replay = lineage.reconstruct_wave48_lineage(trace_id, mission_ledger_records=ledger_records)
    second_replay = lineage.reconstruct_wave48_lineage(trace_id, mission_ledger_records=ledger_records)
    state_replayed = planetary.replay()["matches_current_state"] and continental.replay()["matches_current_state"]

    return {
        "wave": 74,
        "status": "PASS" if all([
            replay["status"] == "PASS",
            second_replay["status"] == "PASS",
            state_replayed,
            interplanetary.replay()["matches_current_state"],
            interplanetary_recovery["event_type"] == "INTERPLANETARY_RECOVERY_COMPLETED",
            contract_registry.get_contract(contract_id)["version"] == "1.0.0",
            civilization_state["digital_twin_status"] == "RECONCILED",
        ]) else "FAIL",
        "interplanetary": "PASS" if (
            interplanetary.replay()["matches_current_state"]
            and interplanetary_recovery["event_type"] == "INTERPLANETARY_RECOVERY_COMPLETED"
            and interplanetary_recovery["caused_by"] == interplanetary_root["event_id"]
        ) else "FAIL",
        "planetary": "PASS" if state_replayed else "FAIL",
        "continental": "PASS" if continental.get_snapshot()["replay_integrity"] == "PASS" else "FAIL",
        "global": "PASS" if global_state["active_events"] else "FAIL",
        "civilization": "PASS" if civilization_state["digital_twin_status"] == "RECONCILED" and civilization_state["caused_by"] == event_id else "FAIL",
        "event_store": "PASS" if replay["valid"] else "FAIL",
        "contract_registry": "PASS" if contract_registry.get_contract(contract_id)["version"] == "1.0.0" else "FAIL",
        "lineage_valid": replay["lineage_valid"],
        "replay_valid": replay["gates"]["replay_valid"] and second_replay["gates"]["replay_valid"],
        "audit_valid": replay["gates"]["audit_valid"] and ledger.verify_integrity(),
        "idempotency_valid": second_replay["event_id"] == event_id and len(lineage.history(trace_id)) == len(records) + 1,
        "rollback_valid": (
            interplanetary.snapshot() != interplanetary_baseline
            and interplanetary_recovery["caused_by"] == interplanetary_root["event_id"]
            and any(item["event_type"] == "GLOBAL_ROLLBACK_APPLIED" for item in records)
        ),
        "recovery_valid": (
            interplanetary_recovery["event_type"] == "INTERPLANETARY_RECOVERY_COMPLETED"
            and any(item["event_type"] == "GLOBAL_RECOVERY_COMPLETED" for item in records)
        ),
        "cross_scale_lineage_valid": all(item.get("payload", {}).get("caused_by") == event_id for item in records),
        "digital_twin_reconciled": civilization_state["digital_twin_status"] == "RECONCILED",
        "event_id": event_id,
        "trace_id": trace_id,
        "decision_id": decision_id,
        "execution_id": execution_id,
        "reconciliation_id": reconciliation_id,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, separators=(",", ":")))



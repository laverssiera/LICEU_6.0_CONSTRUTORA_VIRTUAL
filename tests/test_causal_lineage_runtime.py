import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.causal_lineage_runtime import CausalLineageRuntime


class EventStoreSpy:
    def __init__(self) -> None:
        self.events = []

    def append(self, **kwargs):
        self.events.append(kwargs)


class MissionLedgerSpy:
    def __init__(self) -> None:
        self.entries = []

    def record_lineage_event(self, entry):
        self.entries.append(entry)


def test_reconstruct_connects_the_four_ids_across_cycle() -> None:
    runtime = CausalLineageRuntime()

    context = runtime.start_lineage(event_id="event-break", trace_id="trace-cycle-1")
    runtime.record(
        context,
        event_type="CONTINENTAL_BREAK",
        phase="ruptura",
    )
    context.decision_id = "decision-cycle-1"
    context.causation_id = "event-break"
    runtime.record(
        context,
        event_type="DECISION_CREATED",
        phase="decisao",
    )
    context.execution_id = "execution-cycle-1"
    context.causation_id = "decision-cycle-1"
    runtime.record(
        context,
        event_type="EXECUTION_STARTED",
        phase="execucao",
    )
    context.twin_reconciliation_id = "twinrec-cycle-1"
    context.causation_id = "execution-cycle-1"
    runtime.record(
        context,
        event_type="DIGITAL_TWIN_RECONCILED",
        phase="reconciliacao",
    )

    result = runtime.reconstruct("trace-cycle-1")

    assert result["status"] == "PASS"
    assert result["reconstructable"] is True
    assert result["validation"]["ids"] == {
        "event_id": True,
        "trace_id": True,
        "decision_id": True,
        "execution_id": True,
        "twin_reconciliation_id": True,
    }
    assert [event["phase"] for event in result["events"]] == ["ruptura", "decisao", "execucao", "reconciliacao"]


def test_record_rejects_missing_causal_identifier() -> None:
    runtime = CausalLineageRuntime()

    with pytest.raises(ValueError, match="event_id and trace_id"):
        runtime.start_lineage(event_id="", trace_id="trace-1")


def test_record_rejects_independent_archimedes_ids() -> None:
    runtime = CausalLineageRuntime()
    context = runtime.start_lineage(event_id="archimedes-event-1", trace_id="archimedes-trace-1")
    context.decision_id = "decision-standalone"
    context.execution_id = "execution-standalone"
    context.twin_reconciliation_id = "reconciliation-standalone"

    with pytest.raises(ValueError, match="chained"):
        runtime.record(context, event_type="ARCHIMEDES_EVENT", phase="archimedes")


def test_record_persists_lineage_in_existing_adapters() -> None:
    event_store = EventStoreSpy()
    mission_ledger = MissionLedgerSpy()
    runtime = CausalLineageRuntime(event_store=event_store, mission_ledger=mission_ledger)
    context = runtime.start_lineage("event-1", "trace-1")

    runtime.record(context, event_type="CONTINENTAL_BREAK", phase="ruptura")

    assert event_store.events[0]["trace_id"] == "trace-1"
    assert event_store.events[0]["causation_id"] is None
    assert event_store.events[0]["payload"]["causal_lineage"]["event_id"] == "event-1"
    assert mission_ledger.entries[0]["trace_id"] == "trace-1"


def test_reconstruct_wave48_requires_and_returns_complete_chain() -> None:
    event_store = EventStoreSpy()
    mission_ledger = MissionLedgerSpy()
    runtime = CausalLineageRuntime(event_store=event_store, mission_ledger=mission_ledger)
    context = runtime.start_lineage("evt-cont-0048-001", "trace-cont-0048-001")

    stages = [
        ("DIGITAL_TWIN_UPDATED", "twin-initial", None),
        ("ARCHIMEDES_EVENT", "archimedes", "evt-cont-0048-001"),
        ("EVENT_STORE_PERSISTED", "event_store", "evt-cont-0048-001"),
        ("CEFEIDA_EVENT_PROPAGATED", "cefeida", "evt-cont-0048-001"),
        ("JOHN_DECISION_CREATED", "decision", "evt-cont-0048-001"),
        ("ANCHORS_AUTHORIZED", "anchors", "decision-cont-0048-001"),
        ("OPERA_EXECUTION_STARTED", "execution", "decision-cont-0048-001"),
        ("BIM_INFRASTRUCTURE_UPDATED", "bim", "exec-cont-0048-001"),
        ("FORNECEDORES_IMPACT_RECORDED", "fornecedores", "exec-cont-0048-001"),
        ("ECONOTECH_MITIGATION_RECORDED", "econotech", "exec-cont-0048-001"),
        ("CEA_LESSON_LEARNED", "cea", "exec-cont-0048-001"),
        ("JURIDICOTECH_REVIEWED", "juridicotech", "exec-cont-0048-001"),
        ("HUB_BACKOFFICE_RECONCILED", "backoffice", "exec-cont-0048-001"),
        ("ACADEMIA_LESSON_PUBLISHED", "academia", "exec-cont-0048-001"),
        ("ARCHIMEDES_RECONCILIATION", "reconciliation", "exec-cont-0048-001"),
    ]
    for event_type, phase, causation_id in stages:
        context.causation_id = causation_id
        context.parent_event_id = None if not runtime.history() else "evt-cont-0048-001"
        if phase == "decision":
            context.decision_id = "decision-cont-0048-001"
        if phase in {"execution", "downstream", "reconciliation"}:
            context.execution_id = "exec-cont-0048-001"
        if phase == "reconciliation":
            context.twin_reconciliation_id = "twinrec-cont-0048-001"
            context.reconciliation_event_id = "recon-event-cont-0048-001"
        runtime.record(context, event_type=event_type, phase=phase)

    context.causation_id = "exec-cont-0048-001"
    context.parent_event_id = "evt-cont-0048-001"
    final_twin = runtime.record(
        context,
        event_type="DIGITAL_TWIN_UPDATED",
        phase="final_twin",
        payload={"caused_by": "evt-cont-0048-001"},
    )

    result = runtime.reconstruct_wave48_lineage(
        "trace-cont-0048-001",
        event_store_records=event_store.events,
        mission_ledger_records=mission_ledger.entries,
    )

    assert result["valid"] is True
    assert result["event_id"] == "evt-cont-0048-001"
    assert result["decision_id"] == "decision-cont-0048-001"
    assert result["execution_id"] == "exec-cont-0048-001"
    assert result["reconciliation_id"] == "twinrec-cont-0048-001"
    assert result["reconciliation_event_id"] == "recon-event-cont-0048-001"
    assert result["lineage_valid"] is True
    assert result["idempotency_valid"] is True
    assert result["digital_twin_reconciled"] is True
    assert result["status"] == "PASS"
    assert all(result["gates"].values())
    assert all(monolith["status"] == "PASS" for monolith in result["monoliths"])
    assert result["impact"] == {}
    assert result["mitigation"] == {}
    assert result["lesson_learned"] == {}
    assert final_twin["lineage_id"] != result["chain"][0]["lineage_id"]
    assert final_twin["caused_by"] == result["event_id"]
    assert final_twin["payload"]["caused_by"] == result["event_id"]
    assert len(result["chain"]) == 16

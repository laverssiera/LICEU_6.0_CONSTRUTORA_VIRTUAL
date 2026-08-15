from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import asyncio
import inspect
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4


WAVE48_MONOLITHS = (
    ("ARCHIMEDES", "ARCHIMEDES_EVENT"),
    ("EVENT_STORE", "EVENT_STORE_PERSISTED"),
    ("CEFEIDA", "CEFEIDA_EVENT_PROPAGATED"),
    ("JOHN_DECISION", "JOHN_DECISION_CREATED"),
    ("ANCHORS_GOVERNANCE", "ANCHORS_AUTHORIZED"),
    ("OPERA_EXECUTION", "OPERA_EXECUTION_STARTED"),
    ("BIM_INFRASTRUCTURE", "BIM_INFRASTRUCTURE_UPDATED"),
    ("FORNECEDORES", "FORNECEDORES_IMPACT_RECORDED"),
    ("ECONOTECH", "ECONOTECH_MITIGATION_RECORDED"),
    ("CEA", "CEA_LESSON_LEARNED"),
    ("JURIDICOTECH", "JURIDICOTECH_REVIEWED"),
    ("HUB_BACKOFFICE", "HUB_BACKOFFICE_RECONCILED"),
    ("ACADEMIA", "ACADEMIA_LESSON_PUBLISHED"),
    ("ARCHIMEDES_RECONCILIATION", "ARCHIMEDES_RECONCILIATION"),
)


@dataclass
class CausalLineageContext:
    event_id: str
    trace_id: str
    decision_id: Optional[str] = None
    execution_id: Optional[str] = None
    twin_reconciliation_id: Optional[str] = None
    reconciliation_id: Optional[str] = None
    reconciliation_event_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    causation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    sequence: int = 0
    timestamp: Optional[str] = None
    producer: Optional[str] = None
    consumer: Optional[str] = None
    status: str = "RECORDED"
    mission_id: Optional[str] = None
    case_id: Optional[str] = None
    contract_id: Optional[str] = None
    schema_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        return bool(self.event_id and self.trace_id)

    def to_dict(self) -> Dict[str, Any]:
        return deepcopy(asdict(self))


class CausalLineageRuntime:
    """Runtime compartilhado para propagar e reconstruir lineage causal."""

    def __init__(self, event_store: Any = None, mission_ledger: Any = None) -> None:
        self._records: List[Dict[str, Any]] = []
        self.event_store = event_store
        self.mission_ledger = mission_ledger

    def start_lineage(self, event_id: str, trace_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> CausalLineageContext:
        context = CausalLineageContext(
            event_id=event_id,
            trace_id=trace_id or str(uuid4()),
            correlation_id=trace_id or None,
            metadata=metadata or {},
        )
        if not context.validate():
            raise ValueError("event_id and trace_id are required")
        return context

    def _validate_context_chain(self, context: CausalLineageContext) -> None:
        previous = self.history(context.trace_id)
        previous_ids = {
            identifier
            for record in previous
            for identifier in (
                record.get("event_id"),
                record.get("decision_id"),
                record.get("execution_id"),
                record.get("twin_reconciliation_id"),
                record.get("reconciliation_id"),
                record.get("reconciliation_event_id"),
            )
            if identifier
        }

        if context.causation_id and previous and context.causation_id not in previous_ids:
            raise ValueError("causation_id must reference an existing lineage id in the same trace")

        if context.decision_id and not context.causation_id:
            raise ValueError("decision_id requires a chained causation_id to a prior lineage event")

        if context.execution_id and not context.decision_id and not (
            context.causation_id and context.causation_id in previous_ids
        ):
            raise ValueError("execution_id must be chained to a prior decision_id or causation_id")

        if (context.twin_reconciliation_id or context.reconciliation_id) and not (
            context.execution_id or (context.causation_id and context.causation_id in previous_ids)
        ):
            raise ValueError("reconciliation_id must be chained to a prior execution_id or causation_id")

        if context.reconciliation_id and not context.twin_reconciliation_id:
            context.twin_reconciliation_id = context.reconciliation_id

    def record(
        self,
        context: CausalLineageContext,
        *,
        event_type: str,
        phase: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not context.validate():
            raise ValueError("event_id and trace_id are required")

        self._validate_context_chain(context)

        context = deepcopy(context)
        context.sequence = len(self._records) + 1
        context.correlation_id = context.correlation_id or context.trace_id
        context.timestamp = context.timestamp or datetime.now(timezone.utc).isoformat()
        entry = {
            "lineage_id": str(uuid4()),
            **context.to_dict(),
            "event_type": event_type,
            "phase": phase,
            "status": context.status,
            "timestamp": context.timestamp,
            "payload": deepcopy(payload or {}),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        if payload and payload.get("caused_by"):
            entry["caused_by"] = payload["caused_by"]
        self._records.append(entry)
        self._persist(entry)
        return deepcopy(entry)

    def _persist(self, entry: Dict[str, Any]) -> None:
        payload = {"causal_lineage": deepcopy(entry), **deepcopy(entry["payload"])}
        if self.event_store is not None and hasattr(self.event_store, "append"):
            result = self.event_store.append(
                aggregate_id=entry["trace_id"],
                event_type=entry["event_type"],
                payload=payload,
                correlation_id=entry["trace_id"],
                causation_id=entry.get("causation_id"),
                trace_id=entry["trace_id"],
            )
            if inspect.isawaitable(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(result)
                    else:
                        loop.run_until_complete(result)
                except RuntimeError:
                    asyncio.run(result)
        if self.mission_ledger is not None and hasattr(self.mission_ledger, "record_lineage_event"):
            self.mission_ledger.record_lineage_event(entry)

    def history(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = self._records
        if trace_id is not None:
            records = [record for record in records if record["trace_id"] == trace_id]
        return deepcopy(sorted(records, key=lambda record: record["sequence"]))

    def validate(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        records = self.history(trace_id)
        if not records:
            return {"status": "FAIL", "records": 0, "ids": {}, "connected": False}

        first = records[0]
        trace_values = {record["trace_id"] for record in records}
        required = {
            "event_id": bool(first.get("event_id")),
            "trace_id": len(trace_values) == 1,
            "decision_id": any(record.get("decision_id") for record in records),
            "execution_id": any(record.get("execution_id") for record in records),
            "twin_reconciliation_id": any(record.get("twin_reconciliation_id") for record in records),
        }
        causal_links = all(
            record.get("causation_id") is None or record.get("causation_id") in {
                identifier
                for previous in records[:index]
                for identifier in (
                    previous.get("event_id"),
                    previous.get("decision_id"),
                    previous.get("execution_id"),
                    previous.get("twin_reconciliation_id"),
                )
                if identifier
            }
            for index, record in enumerate(records)
        )
        connected = all(required.values()) and causal_links
        return {
            "status": "PASS" if connected else "FAIL",
            "records": len(records),
            "ids": required,
            "connected": connected,
            "causal_links": causal_links,
            "trace_id": next(iter(trace_values), None),
        }

    @staticmethod
    def _unwrap_record(record: Dict[str, Any]) -> Dict[str, Any]:
        result = record.get("resultado") if isinstance(record.get("resultado"), dict) else None
        if result and result.get("trace_id"):
            return {
                **deepcopy(result),
                "event_type": record.get("porque", "CAUSAL_LINEAGE_EVENT"),
                "timestamp": record.get("quando"),
                "status": record.get("status", "RECORDED"),
            }
        payload = record.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        payload = payload if isinstance(payload, dict) else {}
        lineage = payload.get("causal_lineage") if isinstance(payload.get("causal_lineage"), dict) else None
        return deepcopy(lineage or record)

    @staticmethod
    def _source_records(source: Any) -> List[Dict[str, Any]]:
        if source is None:
            return []
        if isinstance(source, list):
            return [CausalLineageRuntime._unwrap_record(record) for record in source]
        if hasattr(source, "ledger"):
            return [CausalLineageRuntime._unwrap_record(record) for record in source.ledger]
        if hasattr(source, "events"):
            return [CausalLineageRuntime._unwrap_record(record) for record in source.events]
        return []

    @staticmethod
    def _canonical(record: Dict[str, Any]) -> Dict[str, Any]:
        fields = (
            "event_id", "trace_id", "parent_event_id", "causation_id", "correlation_id",
            "decision_id", "execution_id", "twin_reconciliation_id", "reconciliation_id",
            "reconciliation_event_id", "sequence", "event_type", "status", "producer",
            "consumer", "mission_id", "case_id", "contract_id", "schema_id", "timestamp",
        )
        return {field: record.get(field) for field in fields}

    @staticmethod
    def _event_kind(record: Dict[str, Any]) -> str:
        normalized = str(record.get("event_type", "")).upper().replace("-", "_")
        if normalized == "DIGITAL_TWIN_UPDATED":
            return "final_twin" if record.get("reconciliation_event_id") or record.get("twin_reconciliation_id") else "initial_twin"
        if "CEFEIDA" in normalized and ("PROPAG" in normalized or "EVENT" in normalized):
            return "cefeida"
        if "DECISION" in normalized and "JOHN" in normalized:
            return "decision"
        if "ANCHOR" in normalized and ("AUTH" in normalized or "APPROV" in normalized):
            return "anchors"
        if "EXECUTION" in normalized or "OPERA" in normalized and "START" in normalized:
            return "execution"
        if "RECONCIL" in normalized or "ARCHIMEDES" in normalized and "TWIN" in normalized:
            return "reconciliation"
        return "downstream"

    def validate_wave48_lineage(
        self,
        trace_id: str,
        *,
        event_store_records: Optional[List[Dict[str, Any]]] = None,
        mission_ledger_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        event_records = self._source_records(event_store_records) if event_store_records is not None else self.history(trace_id)
        ledger_records = self._source_records(mission_ledger_records) if mission_ledger_records is not None else self.history(trace_id)
        event_records = sorted([record for record in event_records if record.get("trace_id") == trace_id], key=lambda item: item.get("sequence", 0))
        ledger_records = sorted([record for record in ledger_records if record.get("trace_id") == trace_id], key=lambda item: item.get("sequence", 0))
        records = event_records
        reasons: List[str] = []

        if not records:
            reasons.append("trace_not_found")
        if not ledger_records:
            reasons.append("mission_ledger_trace_not_found")
        if event_records and ledger_records:
            if [_canonical for _canonical in map(self._canonical, event_records)] != [self._canonical(record) for record in ledger_records]:
                reasons.append("event_store_mission_ledger_divergence")

        decision_id = next((record.get("decision_id") for record in event_records if record.get("decision_id")), None)
        execution_id = next((record.get("execution_id") for record in event_records if record.get("execution_id")), None)
        kinds = [self._event_kind(record) for record in records]
        if records:
            if records[0].get("parent_event_id") not in (None, ""):
                reasons.append("initial_event_has_parent")
            traces = {record.get("trace_id") for record in records}
            if traces != {trace_id}:
                reasons.append("trace_id_break")
            sequences = [record.get("sequence") for record in records]
            if sequences != list(range(1, len(records) + 1)):
                reasons.append("sequence_break")
            known_ids = set()
            for index, record in enumerate(records):
                if not record.get("event_id") or not record.get("trace_id"):
                    reasons.append(f"missing_required_id:{index}")
                if index > 0 and not record.get("parent_event_id"):
                    reasons.append(f"missing_parent_event_id:{index}")
                if record.get("parent_event_id") and record["parent_event_id"] not in known_ids:
                    reasons.append(f"orphan_parent_event_id:{index}")
                if record.get("causation_id") and record["causation_id"] not in known_ids:
                    reasons.append(f"orphan_causation_id:{index}")
                known_ids.update(value for value in (
                    record.get("event_id"), record.get("decision_id"), record.get("execution_id"),
                    record.get("twin_reconciliation_id"), record.get("reconciliation_event_id"),
                ) if value)

            positions = {kind: kinds.index(kind) for kind in set(kinds)}
            for required_kind in ("initial_twin", "cefeida", "decision", "anchors", "execution", "reconciliation", "final_twin"):
                if required_kind not in positions:
                    reasons.append(f"missing_stage:{required_kind}")
            if "decision" in positions and not records[positions["decision"]].get("decision_id"):
                reasons.append("decision_without_decision_id")
            if "execution" in positions:
                execution = records[positions["execution"]]
                if not execution.get("execution_id"):
                    reasons.append("execution_without_execution_id")
                if not execution.get("decision_id"):
                    reasons.append("execution_without_decision_id")
            if "reconciliation" in positions:
                reconciliation = records[positions["reconciliation"]]
                if not reconciliation.get("execution_id") or reconciliation.get("causation_id") != execution_id:
                    reasons.append("reconciliation_without_execution_or_causation")
            if "final_twin" in positions:
                final_twin = records[positions["final_twin"]]
                if not final_twin.get("reconciliation_event_id"):
                    reasons.append("final_twin_without_reconciliation_event_id")
                if final_twin.get("caused_by") != records[0].get("event_id"):
                    reasons.append("final_twin_without_initial_event_causation")
                if final_twin.get("lineage_id") == records[0].get("lineage_id"):
                    reasons.append("final_twin_must_be_a_distinct_event")
            if any(positions[left] >= positions[right] for left, right in (
                ("initial_twin", "cefeida"), ("cefeida", "decision"), ("decision", "anchors"),
                ("anchors", "execution"), ("execution", "reconciliation"),
                ("reconciliation", "final_twin"),
            ) if left in positions and right in positions):
                reasons.append("causal_sequence_break")

        event_types = [str(record.get("event_type", "")).upper() for record in records]
        monoliths = []
        last_position = -1
        for name, expected_event_type in WAVE48_MONOLITHS:
            try:
                position = event_types.index(expected_event_type)
            except ValueError:
                position = -1
            passed = position > last_position
            monoliths.append({"name": name, "event_type": expected_event_type, "status": "PASS" if passed else "FAIL"})
            if passed:
                last_position = position
            else:
                reasons.append(f"missing_or_out_of_order_monolith:{name}")

        reconciliation_id = next((record.get("reconciliation_id", record.get("twin_reconciliation_id")) for record in records if record.get("reconciliation_id") or record.get("twin_reconciliation_id")), None)
        reconciliation_event_id = next((record.get("reconciliation_event_id", reconciliation_id) for record in records if record.get("reconciliation_event_id") or record.get("twin_reconciliation_id") or record.get("reconciliation_id")), None)
        lineage_valid = not reasons
        replay_valid = bool(records) and not any(reason in reasons for reason in ("sequence_break", "event_store_mission_ledger_divergence"))
        audit_valid = bool(records) and all(record.get("timestamp") and record.get("status") for record in records) and not bool(
            [reason for reason in reasons if reason.startswith("event_store_mission_ledger")]
        )
        rollback_valid = lineage_valid and records[0].get("event_id") == event_records[0].get("event_id") if event_records else False
        recovery_valid = lineage_valid and "reconciliation" in kinds and "final_twin" in kinds
        digital_twin_reconciled = "final_twin" in kinds and "reconciliation" in kinds and not any(
            reason.startswith("final_twin_") for reason in reasons
        )
        gates = {
            "lineage_valid": lineage_valid,
            "replay_valid": replay_valid,
            "audit_valid": audit_valid,
            "idempotency_valid": len({record.get("sequence") for record in records}) == len(records) if records else False,
            "rollback_valid": rollback_valid,
            "recovery_valid": recovery_valid,
            "digital_twin_reconciled": digital_twin_reconciled,
        }
        def event_payload(event_type: str) -> Dict[str, Any]:
            record = next((item for item in records if item.get("event_type") == event_type), {})
            return deepcopy(record.get("payload", {}))

        return {
            "valid": not reasons,
            "lineage_valid": lineage_valid,
            "wave": "WAVE_48",
            "scope": "CONTINENTAL_BUTTERFLY_EFFECT",
            "case": records[0].get("case_id") if records else None,
            "event_id": records[0].get("event_id") if records else None,
            "trace_id": trace_id,
            "decision_id": decision_id,
            "execution_id": execution_id,
            "reconciliation_id": reconciliation_id,
            "reconciliation_event_id": reconciliation_event_id,
            "impact": event_payload("BIM_INFRASTRUCTURE_UPDATED"),
            "mitigation": event_payload("ECONOTECH_MITIGATION_RECORDED"),
            "lesson_learned": event_payload("CEA_LESSON_LEARNED"),
            "chain": records,
            "monoliths": monoliths,
            "gates": gates,
            "status": "PASS" if all(gates.values()) else "FAIL",
            "divergence": ["event_store_mission_ledger_divergence"] if "event_store_mission_ledger_divergence" in reasons else [],
            "idempotency_valid": gates["idempotency_valid"],
            "digital_twin_reconciled": gates["digital_twin_reconciled"],
            "reasons": reasons,
        }

    def reconstruct_wave48_lineage(self, trace_id: str, **sources: Any) -> Dict[str, Any]:
        """Reconstructs Wave 48 from the existing Event Store and Mission Ledger records."""
        return self.validate_wave48_lineage(trace_id, **sources)

    async def reconstruct_wave48_lineage_async(self, trace_id: str) -> Dict[str, Any]:
        """Loads the existing Event Store and Mission Ledger before validating."""
        event_records: List[Dict[str, Any]] = []
        if self.event_store is not None and hasattr(self.event_store, "get_events_by_trace"):
            event_records = await self.event_store.get_events_by_trace(trace_id)
        ledger_records = self.mission_ledger.get_ledger() if self.mission_ledger is not None and hasattr(self.mission_ledger, "get_ledger") else []
        return self.reconstruct_wave48_lineage(
            trace_id,
            event_store_records=event_records,
            mission_ledger_records=ledger_records,
        )

    def reconstruct_lineage(self, trace_id: str) -> Dict[str, Any]:
        records = self.history(trace_id)
        validation = self.validate(trace_id)
        latest = records[-1] if records else {}
        reconciliation_id = next((record.get("reconciliation_id", record.get("twin_reconciliation_id")) for record in records if record.get("reconciliation_id") or record.get("twin_reconciliation_id")), None)
        return {
            "event_id": records[0].get("event_id") if records else None,
            "trace_id": trace_id,
            "decision_id": next((record.get("decision_id") for record in records if record.get("decision_id")), None),
            "execution_id": next((record.get("execution_id") for record in records if record.get("execution_id")), None),
            "reconciliation_id": reconciliation_id,
            "twin_reconciliation_id": next((record.get("twin_reconciliation_id") for record in records if record.get("twin_reconciliation_id")), None),
            "lineage_valid": validation["connected"],
            "validation": validation,
            "events": records,
            "latest_phase": latest.get("phase"),
        }

    def reconstruct(self, trace_id: str) -> Dict[str, Any]:
        result = self.reconstruct_lineage(trace_id)
        result["status"] = "PASS" if result["lineage_valid"] else "FAIL"
        result["reconstructable"] = result["lineage_valid"]
        return result


causal_lineage_runtime = CausalLineageRuntime()

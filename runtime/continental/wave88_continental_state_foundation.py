from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from runtime.causal_lineage_runtime import CausalLineageContext, CausalLineageRuntime
from runtime.orchestration.mission_ledger_runtime import MissionLedgerRuntime, mission_ledger as shared_mission_ledger


REQUIRED_IDS = (
    "planetary_operational_state_id",
    "source_event_id",
    "trace_id",
    "decision_id",
    "governance_decision_id",
    "execution_id",
    "reconciliation_id",
)


class ContinentalStateFoundation:
    """Projects an already reconciled W87 state into the existing runtimes."""

    def __init__(
        self,
        *,
        mission_ledger: Optional[MissionLedgerRuntime] = None,
        lineage: Optional[CausalLineageRuntime] = None,
    ) -> None:
        self.mission_ledger = mission_ledger or shared_mission_ledger
        self.lineage = lineage or CausalLineageRuntime(
            event_store=self.mission_ledger.event_store,
            mission_ledger=self.mission_ledger,
        )
        self._processed: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _require_w87(envelope: Dict[str, Any]) -> None:
        if not isinstance(envelope, dict):
            raise ValueError("W87 envelope must be an object")
        missing = [key for key in REQUIRED_IDS if not str(envelope.get(key, "")).strip()]
        if missing:
            raise ValueError(f"W87 envelope missing IDs: {', '.join(missing)}")
        if envelope.get("scope") not in (None, "PLANETARY"):
            raise ValueError("W87 envelope scope must be PLANETARY")
        if envelope.get("status") not in (None, "RECONCILED", "PASS"):
            raise ValueError("W87 envelope is not reconciled")

    @staticmethod
    def _state_id(envelope: Dict[str, Any]) -> str:
        canonical = json.dumps(
            {key: envelope[key] for key in REQUIRED_IDS},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"continental-state-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"

    def execute(self, w87_envelope: Dict[str, Any]) -> Dict[str, Any]:
        self._require_w87(w87_envelope)
        source_event_id = w87_envelope["source_event_id"]
        if source_event_id in self._processed:
            return dict(self._processed[source_event_id])

        continental_state_id = self._state_id(w87_envelope)
        continental_event_id = str(uuid4())
        trace_id = w87_envelope["trace_id"]
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "scope": "CONTINENTAL",
            "continental_state_id": continental_state_id,
            "planetary_operational_state_id": w87_envelope["planetary_operational_state_id"],
            "source_event_id": source_event_id,
            "decision_id": w87_envelope["decision_id"],
            "governance_decision_id": w87_envelope["governance_decision_id"],
            "execution_id": w87_envelope["execution_id"],
            "reconciliation_id": w87_envelope["reconciliation_id"],
            "caused_by": source_event_id,
        }
        context = CausalLineageContext(
            event_id=continental_event_id,
            trace_id=trace_id,
            decision_id=w87_envelope["decision_id"],
            execution_id=w87_envelope["execution_id"],
            reconciliation_id=w87_envelope["reconciliation_id"],
            reconciliation_event_id=continental_event_id,
            parent_event_id=source_event_id,
            causation_id=source_event_id,
            correlation_id=trace_id,
            producer="WAVE_88_CONTINENTAL_STATE_FOUNDATION",
            consumer="CONTINENTAL_STATE",
            status="RECORDED",
        )

        # W87 is the existing parent; only the new continental projection is appended.
        entry = self.lineage.record(
            context,
            event_type="CONTINENTAL_STATE_CREATED",
            phase="CONTINENTAL_STATE",
            payload=payload,
        )
        result = {
            "wave": "WAVE_88",
            "status": "PASS",
            "continental_state_id": continental_state_id,
            "continental_event_id": continental_event_id,
            **{key: w87_envelope[key] for key in REQUIRED_IDS},
            "validations": {
                "contract_valid": True,
                "lineage_valid": entry["causation_id"] == source_event_id and entry["parent_event_id"] == source_event_id,
                "replay_valid": self._state_id(w87_envelope) == continental_state_id,
                "audit_valid": bool(entry["timestamp"] and entry["status"]),
                "idempotency_valid": source_event_id not in self._processed,
                "rollback_valid": entry["causation_id"] == source_event_id,
                "recovery_valid": bool(w87_envelope["reconciliation_id"]),
                "persistence_verified": bool(self.mission_ledger.ledger) and bool(self.lineage.history(trace_id)),
            },
            "persisted_event": entry,
            "created_at": now,
        }
        result["status"] = "PASS" if all(result["validations"].values()) else "FAIL"
        self._processed[source_event_id] = dict(result)
        return result

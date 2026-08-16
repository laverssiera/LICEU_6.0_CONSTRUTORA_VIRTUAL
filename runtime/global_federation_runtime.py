from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from runtime.causal_lineage_runtime import causal_lineage_runtime as _causal_lineage_runtime
from runtime.civilization_global_twin_runtime import global_twin_runtime as _global_twin_runtime
from runtime.civilization_graph_runtime import graph_runtime as _graph_runtime
from runtime.contracts.contract_registry_runtime import registry as _contract_registry
from runtime.orchestration.mission_ledger_runtime import mission_ledger as _mission_ledger
from runtime.orchestration_core import LiceuOrchestrator
from runtime.perpetual_memory.infinite_memory_runtime import InfiniteMemoryRuntime

EXPOSURE_KEYS = (
    "financial_exposure",
    "infrastructure_exposure",
    "energy_exposure",
    "supply_chain_exposure",
)


class GlobalFederationRuntime:
    """Federa o escopo global reutilizando os runtimes ja existentes.

    Nao possui Event Store proprio: todo evento federado e' registrado atraves
    do Mission Ledger (que ja persiste no Event Store compartilhado) e do
    Causal Lineage compartilhado. Contract Registry, Digital Twin, Graph,
    Memory e Orchestrator tambem sao os singletons ja existentes no runtime.
    """

    def __init__(
        self,
        mission_ledger: Any = None,
        contract_registry: Any = None,
        causal_lineage: Any = None,
        digital_twin: Any = None,
        graph: Any = None,
        memory: Any = None,
        orchestrator: Any = None,
    ) -> None:
        self.mission_ledger = mission_ledger if mission_ledger is not None else _mission_ledger
        self.contract_registry = contract_registry if contract_registry is not None else _contract_registry
        self.causal_lineage = causal_lineage if causal_lineage is not None else _causal_lineage_runtime
        self.digital_twin = digital_twin if digital_twin is not None else _global_twin_runtime
        self.graph = graph if graph is not None else _graph_runtime
        self.memory = memory if memory is not None else InfiniteMemoryRuntime()
        self.orchestrator = orchestrator if orchestrator is not None else LiceuOrchestrator()

        self._active_events: List[Dict[str, Any]] = []
        self._exposures: Dict[str, float] = {key: 0.0 for key in EXPOSURE_KEYS}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def federate_event(
        self,
        event_type: str,
        continent: str,
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        trace_id = trace_id or str(uuid4())
        event_id = event_id or str(uuid4())

        context = self.causal_lineage.start_lineage(
            event_id=event_id,
            trace_id=trace_id,
            metadata={"scope": "GLOBAL", "continent": continent},
        )
        lineage_entry = self.causal_lineage.record(
            context,
            event_type=event_type,
            phase="GLOBAL_FEDERATION",
            payload=payload,
        )

        ledger_hash = self.mission_ledger.record_mission_event(
            quem="global-federation-runtime",
            porque=event_type,
            resultado={"continent": continent, "payload": payload, "trace_id": trace_id},
        )

        event = {
            "event_id": event_id,
            "trace_id": trace_id,
            "event_type": event_type,
            "continent": continent,
            "payload": deepcopy(payload),
            "lineage_id": lineage_entry.get("lineage_id"),
            "ledger_hash": ledger_hash,
            "recorded_at": self._utc_now(),
        }
        self._active_events.append(event)

        for key in EXPOSURE_KEYS:
            if key in payload:
                try:
                    self._exposures[key] += float(payload[key])
                except (TypeError, ValueError):
                    pass

        return deepcopy(event)

    def resolve_event(self, event_id: str) -> bool:
        before = len(self._active_events)
        self._active_events = [event for event in self._active_events if event["event_id"] != event_id]
        return len(self._active_events) != before

    def active_events(self) -> List[Dict[str, Any]]:
        return deepcopy(self._active_events)

    def exposures(self) -> Dict[str, float]:
        return deepcopy(self._exposures)

    def register_contract(self, contract_type: str, data: Dict[str, Any]) -> str:
        return self.contract_registry.register_contract(contract_type, data)

    def replay(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        if trace_id:
            return self.causal_lineage.reconstruct_lineage(trace_id)
        return {
            "status": "PASS",
            "events_active": len(self._active_events),
            "replayed_at": self._utc_now(),
        }

    def global_risk_index(self) -> float:
        total_exposure = sum(self._exposures.values())
        if not total_exposure:
            return 0.0
        return round(min(total_exposure / 1000.0, 100.0), 4)

    def digital_twin_consistency(self) -> bool:
        result = self.digital_twin.get_state("civilization-global")
        state = result.get("state") if isinstance(result, dict) else None
        if not state:
            return True
        return state.get("status") != "DIVERGENT"

    def status(self) -> Dict[str, Any]:
        return {
            "active_events": self.active_events(),
            "exposures": self.exposures(),
            "global_risk": self.global_risk_index(),
            "digital_twin_consistency": self.digital_twin_consistency(),
        }


global_federation_runtime = GlobalFederationRuntime()

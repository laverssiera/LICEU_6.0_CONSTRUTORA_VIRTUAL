from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from runtime.global_causal_lineage_runtime import global_causal_lineage_runtime as _default_global_lineage
from runtime.global_federation_runtime import GlobalFederationRuntime
from runtime.global_federation_runtime import global_federation_runtime as _default_federation


class GlobalStateRuntime:
    """Estado global consolidado, equivalente ao /civilization/state porem em escopo /global/state.

    Nao possui Event Store, Contract Registry, Mission Ledger, Causal Lineage,
    Replay, Digital Twin, Graph, Memory ou Orchestrator proprios: tudo e'
    projetado a partir do GlobalFederationRuntime, que reutiliza os runtimes
    ja existentes no ecossistema.
    """

    def __init__(self, federation: Optional[GlobalFederationRuntime] = None) -> None:
        self._federation = federation or _default_federation
        self._global_lineage = _default_global_lineage
        self._continents: List[str] = []
        self._active_decisions: List[Dict[str, Any]] = []

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def register_continent(self, continent: str) -> List[str]:
        if continent not in self._continents:
            self._continents.append(continent)
        return list(self._continents)

    def unregister_continent(self, continent: str) -> List[str]:
        self._continents = [item for item in self._continents if item != continent]
        return list(self._continents)

    def register_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        entry = {**decision, "registered_at": self._utc_now()}
        self._active_decisions.append(entry)
        return deepcopy(entry)

    def resolve_decision(self, decision_id: str) -> bool:
        before = len(self._active_decisions)
        self._active_decisions = [
            decision for decision in self._active_decisions if decision.get("decision_id") != decision_id
        ]
        return len(self._active_decisions) != before

    def federate_event(
        self,
        event_type: str,
        continent: str,
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.register_continent(continent)
        return self._federation.federate_event(
            event_type=event_type,
            continent=continent,
            payload=payload,
            trace_id=trace_id,
        )

    def get_state(self) -> Dict[str, Any]:
        status = self._federation.status()
        exposures = status["exposures"]

        return {
            "scope": "global",
            "continents": list(self._continents),
            "active_events": status["active_events"],
            "financial_exposure": exposures["financial_exposure"],
            "infrastructure_exposure": exposures["infrastructure_exposure"],
            "energy_exposure": exposures["energy_exposure"],
            "supply_chain_exposure": exposures["supply_chain_exposure"],
            "global_risk": status["global_risk"],
            "active_decisions": deepcopy(self._active_decisions),
            "digital_twin_consistency": status["digital_twin_consistency"],
        }

    def replay(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        return self._federation.replay(trace_id=trace_id)

    def validate_global_lineage(self, **kwargs: Any) -> Dict[str, Any]:
        return self._global_lineage.validate_global_lineage(**kwargs)

    def get_snapshot(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        state = self.get_state()
        state["replay"] = self.replay(trace_id=trace_id)
        state["snapshot_at"] = self._utc_now()
        return state


global_state_runtime = GlobalStateRuntime()


def get_global_state(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = global_state_runtime.get_state()
    if context:
        state["context"] = context
    return state

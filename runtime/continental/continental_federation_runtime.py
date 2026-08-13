from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ContinentalFederationRuntime:
    """Federa Event Stores de múltiplos Earth Runtimes e mantém Contract Registry continental."""

    def __init__(self) -> None:
        self._event_store: List[Dict[str, Any]] = []
        self._contract_registry: Dict[str, Dict[str, Any]] = {}
        self._lineage: List[Dict[str, Any]] = []
        self._active = True

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def is_active(self) -> bool:
        return self._active

    def activate(self) -> None:
        self._active = True

    # ── Event Store Federation ────────────────────────────────────────────────

    def federate_event(
        self,
        event_type: str,
        source_earth_runtime: str,
        continent: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "source_earth_runtime": source_earth_runtime,
            "continent": continent,
            "payload": payload or {},
            "timestamp": self._utc_now(),
            "federation_status": "FEDERATED",
            "audit": {
                "status": "PASS",
                "recorded_at": self._utc_now(),
                "source": "continental.federation.runtime",
            },
        }
        self._event_store.append(event)

        self._record_lineage(
            event_id=event["event_id"],
            event_type=event_type,
            origin=source_earth_runtime,
            scope="CONTINENTAL",
            continent=continent,
        )

        return deepcopy(event)

    def propagate_continental_event(
        self,
        event_type: str,
        origin_continent: str,
        target_continents: Optional[List[str]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        propagation_id = str(uuid4())
        targets = target_continents or []
        propagations = []

        for target in targets:
            prop_event = self.federate_event(
                event_type="CONTINENTAL_EVENT_PROPAGATED",
                source_earth_runtime=f"continental.{origin_continent.lower()}",
                continent=target,
                payload={
                    "origin_continent": origin_continent,
                    "target_continent": target,
                    "original_event_type": event_type,
                    "propagation_id": propagation_id,
                    **(payload or {}),
                },
            )
            propagations.append(prop_event)

        return {
            "propagation_id": propagation_id,
            "origin_continent": origin_continent,
            "targets": targets,
            "propagations_count": len(propagations),
            "propagated_at": self._utc_now(),
        }

    # ── Contract Registry ─────────────────────────────────────────────────────

    def register_contract(
        self,
        contract_id: str,
        contract_type: str,
        parties: List[str],
        scope: str = "CONTINENTAL",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entry = {
            "contract_id": contract_id,
            "contract_type": contract_type,
            "parties": parties,
            "scope": scope,
            "status": "ACTIVE",
            "registered_at": self._utc_now(),
            "metadata": metadata or {},
        }
        self._contract_registry[contract_id] = entry
        return deepcopy(entry)

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        entry = self._contract_registry.get(contract_id)
        return deepcopy(entry) if entry else None

    def list_contracts(self) -> List[Dict[str, Any]]:
        return [deepcopy(c) for c in self._contract_registry.values()]

    # ── Lineage ───────────────────────────────────────────────────────────────

    def _record_lineage(
        self,
        event_id: str,
        event_type: str,
        origin: str,
        scope: str,
        continent: str,
    ) -> None:
        self._lineage.append(
            {
                "lineage_id": str(uuid4()),
                "event_id": event_id,
                "event_type": event_type,
                "origin": origin,
                "scope": scope,
                "continent": continent,
                "recorded_at": self._utc_now(),
            }
        )

    def get_lineage(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._lineage[-limit:] if limit else self._lineage
        return deepcopy(data)

    # ── Audit & Replay ────────────────────────────────────────────────────────

    def history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._event_store[-limit:] if limit else self._event_store
        return deepcopy(data)

    def replay(self) -> Dict[str, Any]:
        return {
            "status": "PASS",
            "events_processed": len(self._event_store),
            "lineage_entries": len(self._lineage),
            "contracts_registered": len(self._contract_registry),
            "first_event_id": self._event_store[0]["event_id"] if self._event_store else None,
            "last_event_id": self._event_store[-1]["event_id"] if self._event_store else None,
            "replayed_at": self._utc_now(),
        }

    def audit_status(self) -> str:
        for event in self._event_store:
            audit = event.get("audit")
            if not isinstance(audit, dict) or audit.get("status") != "PASS":
                return "FAIL"
        return "PASS"

    def status(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "events_federated": len(self._event_store),
            "contracts_registered": len(self._contract_registry),
            "lineage_entries": len(self._lineage),
            "audit_status": self.audit_status(),
        }


continental_federation_runtime = ContinentalFederationRuntime()

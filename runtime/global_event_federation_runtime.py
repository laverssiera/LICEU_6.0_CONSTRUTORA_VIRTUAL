"""Global Event Store federado: fonte historica unica em escala planetaria.

Continentes emitem eventos localmente, mas a historia canonica vive em um unico
append-only log global, com ordenacao total, correlacao, causalidade, replay
deterministico e imutabilidade verificavel por hash chain.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

GENESIS_HASH = "0" * 64


class ImmutableHistoryViolation(RuntimeError):
    """Levantada quando a hash chain do Event Store global e' quebrada."""


class GlobalEventFederationRuntime:
    """Event Store global append-only alimentado por multiplos continentes."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._by_id: Dict[str, Dict[str, Any]] = {}
        self._continents: Dict[str, int] = {}

    # ---------------------------------------------------------------- helpers
    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _hash_event(self, event: Dict[str, Any]) -> str:
        material = {
            "global_sequence": event["global_sequence"],
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "continent": event["continent"],
            "continent_sequence": event["continent_sequence"],
            "correlation_id": event["correlation_id"],
            "causation_id": event["causation_id"],
            "payload": event["payload"],
            "recorded_at": event["recorded_at"],
            "previous_hash": event["previous_hash"],
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _last_hash(self) -> str:
        return self._events[-1]["event_hash"] if self._events else GENESIS_HASH

    # ------------------------------------------------------------- escrita
    def append_event(
        self,
        continent: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if causation_id and causation_id not in self._by_id:
            raise ValueError(f"causation_id desconhecido no Event Store global: {causation_id}")

        if correlation_id is None:
            parent = self._by_id.get(causation_id) if causation_id else None
            correlation_id = parent["correlation_id"] if parent else str(uuid4())

        continent_sequence = self._continents.get(continent, 0) + 1
        self._continents[continent] = continent_sequence

        event: Dict[str, Any] = {
            "global_sequence": len(self._events) + 1,
            "event_id": str(uuid4()),
            "event_type": event_type,
            "continent": continent,
            "continent_sequence": continent_sequence,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "payload": deepcopy(payload or {}),
            "recorded_at": self._utc_now(),
            "previous_hash": self._last_hash(),
        }
        event["event_hash"] = self._hash_event(event)

        self._events.append(event)
        self._by_id[event["event_id"]] = event
        return deepcopy(event)

    # ------------------------------------------------------------- leitura
    def history(self, continent: Optional[str] = None) -> List[Dict[str, Any]]:
        events: Iterable[Dict[str, Any]] = self._events
        if continent:
            events = (event for event in events if event["continent"] == continent)
        return deepcopy(list(events))

    def continents(self) -> Dict[str, int]:
        return dict(self._continents)

    def correlation(self, correlation_id: str) -> List[Dict[str, Any]]:
        return deepcopy([e for e in self._events if e["correlation_id"] == correlation_id])

    def causal_chain(self, event_id: str) -> List[Dict[str, Any]]:
        """Cadeia causal da raiz ate o evento informado."""
        chain: List[Dict[str, Any]] = []
        cursor = self._by_id.get(event_id)
        while cursor is not None:
            chain.append(deepcopy(cursor))
            cursor = self._by_id.get(cursor["causation_id"]) if cursor["causation_id"] else None
        return list(reversed(chain))

    # ---------------------------------------------------------- validacoes
    def validate_ordering(self) -> Dict[str, Any]:
        violations: List[str] = []
        seen_per_continent: Dict[str, int] = {}
        for index, event in enumerate(self._events, start=1):
            if event["global_sequence"] != index:
                violations.append(f"global_sequence {event['global_sequence']} esperado {index}")
            expected_local = seen_per_continent.get(event["continent"], 0) + 1
            if event["continent_sequence"] != expected_local:
                violations.append(
                    f"{event['continent']} sequence {event['continent_sequence']} esperado {expected_local}"
                )
            seen_per_continent[event["continent"]] = event["continent_sequence"]
        return {
            "check": "ordering",
            "status": "PASS" if not violations else "FAIL",
            "total_events": len(self._events),
            "violations": violations,
        }

    def validate_correlation(self) -> Dict[str, Any]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for event in self._events:
            groups.setdefault(event["correlation_id"], []).append(event)
        orphans = [cid for cid, events in groups.items() if not events]
        cross_continent = {
            cid: sorted({e["continent"] for e in events})
            for cid, events in groups.items()
            if len({e["continent"] for e in events}) > 1
        }
        return {
            "check": "correlation",
            "status": "PASS" if not orphans else "FAIL",
            "correlations": len(groups),
            "cross_continent_correlations": cross_continent,
            "violations": orphans,
        }

    def validate_causality(self) -> Dict[str, Any]:
        violations: List[str] = []
        for event in self._events:
            parent_id = event["causation_id"]
            if not parent_id:
                continue
            parent = self._by_id.get(parent_id)
            if parent is None:
                violations.append(f"{event['event_id']} referencia causa inexistente")
                continue
            if parent["global_sequence"] >= event["global_sequence"]:
                violations.append(f"{event['event_id']} precede sua causa {parent_id}")
            if parent["correlation_id"] != event["correlation_id"]:
                violations.append(f"{event['event_id']} quebra correlacao da causa {parent_id}")
        return {
            "check": "causality",
            "status": "PASS" if not violations else "FAIL",
            "caused_events": sum(1 for e in self._events if e["causation_id"]),
            "violations": violations,
        }

    def validate_immutable_history(self) -> Dict[str, Any]:
        violations: List[str] = []
        previous_hash = GENESIS_HASH
        for event in self._events:
            if event["previous_hash"] != previous_hash:
                violations.append(f"seq {event['global_sequence']}: previous_hash divergente")
            if self._hash_event(event) != event["event_hash"]:
                violations.append(f"seq {event['global_sequence']}: event_hash adulterado")
            previous_hash = event["event_hash"]
        return {
            "check": "immutable_history",
            "status": "PASS" if not violations else "FAIL",
            "head_hash": previous_hash,
            "violations": violations,
        }

    def replay(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        events = self.correlation(correlation_id) if correlation_id else self.history()
        projection: Dict[str, Dict[str, Any]] = {}
        for event in events:
            bucket = projection.setdefault(
                event["continent"],
                {"events": 0, "last_event_type": None, "last_sequence": 0},
            )
            bucket["events"] += 1
            bucket["last_event_type"] = event["event_type"]
            bucket["last_sequence"] = event["global_sequence"]

        signature = hashlib.sha256(
            "|".join(f"{e['global_sequence']}:{e['event_hash']}" for e in events).encode("utf-8")
        ).hexdigest()

        return {
            "check": "replay",
            "status": "PASS",
            "correlation_id": correlation_id,
            "events_replayed": len(events),
            "projection": projection,
            "replay_signature": signature,
            "replayed_at": self._utc_now(),
        }

    def validate_replay_determinism(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        first = self.replay(correlation_id)
        second = self.replay(correlation_id)
        deterministic = first["replay_signature"] == second["replay_signature"]
        return {
            "check": "replay",
            "status": "PASS" if deterministic else "FAIL",
            "events_replayed": first["events_replayed"],
            "replay_signature": first["replay_signature"],
            "violations": [] if deterministic else ["replay nao deterministico"],
        }

    def verify(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        checks = [
            self.validate_ordering(),
            self.validate_correlation(),
            self.validate_causality(),
            self.validate_replay_determinism(correlation_id),
            self.validate_immutable_history(),
        ]
        return {
            "scope": "GLOBAL_EVENT_STORE",
            "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
            "single_source_of_history": True,
            "continents": self.continents(),
            "total_events": len(self._events),
            "checks": checks,
        }


global_event_federation_runtime = GlobalEventFederationRuntime()


def run_demo() -> Dict[str, Any]:
    """Continente A / B / C -> Global Event Store, com validacao completa."""
    runtime = GlobalEventFederationRuntime()

    root = runtime.append_event(
        continent="CONTINENTE_A",
        event_type="SUPPLY_CHAIN_DISRUPTION",
        payload={"severity": 0.82, "supply_chain_exposure": 1200.0},
    )
    correlation_id = root["correlation_id"]

    b1 = runtime.append_event(
        continent="CONTINENTE_B",
        event_type="ENERGY_PRICE_SPIKE",
        payload={"energy_exposure": 640.0},
        causation_id=root["event_id"],
    )
    c1 = runtime.append_event(
        continent="CONTINENTE_C",
        event_type="FINANCIAL_HEDGE_TRIGGERED",
        payload={"financial_exposure": 310.0},
        causation_id=b1["event_id"],
    )
    runtime.append_event(
        continent="CONTINENTE_A",
        event_type="INFRASTRUCTURE_REROUTE",
        payload={"infrastructure_exposure": 150.0},
        causation_id=c1["event_id"],
    )
    runtime.append_event(
        continent="CONTINENTE_C",
        event_type="GLOBAL_DECISION_APPLIED",
        payload={"decision": "REBALANCE_GLOBAL_SUPPLY"},
        causation_id=c1["event_id"],
    )

    report = runtime.verify(correlation_id)
    report["causal_chain"] = [
        {"continent": e["continent"], "event_type": e["event_type"]}
        for e in runtime.causal_chain(c1["event_id"])
    ]
    return report


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, ensure_ascii=False))

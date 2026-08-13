from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from runtime.continental.continental_state_runtime import continental_state_runtime
from runtime.continental.continental_federation_runtime import continental_federation_runtime
from runtime.continental.continental_event_projection_runtime import continental_event_projection_runtime
from runtime.continental.continental_dependency_runtime import continental_dependency_runtime


class ContinentalGovernanceRuntime:
    """Avalia políticas, mantém auditoria e coordena a governança continental."""

    def __init__(self) -> None:
        self._policies: Dict[str, Dict[str, Any]] = {}
        self._decisions: List[Dict[str, Any]] = []
        self._audit_log: List[Dict[str, Any]] = []
        self._active = True

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def activate(self) -> None:
        self._active = True

    def is_active(self) -> bool:
        return self._active

    # ── Policy Registry ───────────────────────────────────────────────────────

    def register_policy(
        self,
        policy_id: str,
        policy_type: str,
        continent: str,
        rules: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        entry = {
            "policy_id": policy_id,
            "policy_type": policy_type,
            "continent": continent,
            "rules": rules or {},
            "description": description,
            "status": "ACTIVE",
            "registered_at": self._utc_now(),
        }
        self._policies[policy_id] = entry
        self._audit("POLICY_REGISTERED", {"policy_id": policy_id, "continent": continent})
        return deepcopy(entry)

    def evaluate_policy(
        self,
        policy_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        policy = self._policies.get(policy_id)
        if not policy:
            return {"policy_id": policy_id, "result": "NOT_FOUND", "evaluated_at": self._utc_now()}

        result = self._run_policy_rules(policy, context or {})

        evaluation = {
            "evaluation_id": str(uuid4()),
            "policy_id": policy_id,
            "continent": policy["continent"],
            "result": result,
            "context": context or {},
            "evaluated_at": self._utc_now(),
        }

        self._audit("CONTINENTAL_POLICY_EVALUATED", evaluation)
        continental_event_projection_runtime.project_policy_evaluated(
            continent=policy["continent"],
            policy_id=policy_id,
            result=result,
        )

        return deepcopy(evaluation)

    def _run_policy_rules(self, policy: Dict[str, Any], context: Dict[str, Any]) -> str:
        rules = policy.get("rules", {})
        if not rules:
            return "COMPLIANT"

        # Avaliação simples: verifica thresholds declarados nas regras
        for rule_key, rule_value in rules.items():
            context_value = context.get(rule_key)
            if context_value is None:
                continue
            if isinstance(rule_value, dict):
                max_val = rule_value.get("max")
                min_val = rule_value.get("min")
                if max_val is not None and float(context_value) > float(max_val):
                    return "VIOLATION"
                if min_val is not None and float(context_value) < float(min_val):
                    return "VIOLATION"

        return "COMPLIANT"

    # ── Decision Engine ───────────────────────────────────────────────────────

    def create_decision(
        self,
        continent: str,
        decision_type: str,
        rationale: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        decision = {
            "decision_id": str(uuid4()),
            "continent": continent,
            "decision_type": decision_type,
            "rationale": rationale,
            "context": context or {},
            "status": "CREATED",
            "created_at": self._utc_now(),
        }
        self._decisions.append(decision)

        self._audit("CONTINENTAL_DECISION_CREATED", decision)
        continental_event_projection_runtime.project_decision_created(
            continent=continent,
            decision_id=decision["decision_id"],
            context=context or {},
        )
        continental_federation_runtime.federate_event(
            event_type="CONTINENTAL_DECISION_CREATED",
            source_earth_runtime=f"continental.governance.{continent.lower()}",
            continent=continent,
            payload=decision,
        )

        return deepcopy(decision)

    # ── Continent Lifecycle ───────────────────────────────────────────────────

    def create_continent(self, continent: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        continental_state_runtime.update_continental_state({"continents": {continent: {"status": "CREATED", **(metadata or {})}}})
        continental_federation_runtime.federate_event(
            event_type="CONTINENT_CREATED",
            source_earth_runtime="continental.governance",
            continent=continent,
            payload={"continent": continent, **(metadata or {})},
        )
        continental_event_projection_runtime.project_continent_created(continent=continent, metadata=metadata)
        self._audit("CONTINENT_CREATED", {"continent": continent})
        return {"continent": continent, "status": "CREATED", "created_at": self._utc_now()}

    def register_region(self, continent: str, region: str, earth_runtime_id: str) -> Dict[str, Any]:
        state_entry = continental_state_runtime.register_earth_runtime(
            continent=continent,
            earth_runtime_id=earth_runtime_id,
            region=region,
        )
        continental_event_projection_runtime.project_region_registered(
            continent=continent,
            region=region,
            earth_runtime_id=earth_runtime_id,
        )
        self._audit("REGION_REGISTERED", {"continent": continent, "region": region, "earth_runtime_id": earth_runtime_id})
        return state_entry

    # ── Risk Governance ───────────────────────────────────────────────────────

    def evaluate_risk(self, continent: str, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        risk_report = continental_dependency_runtime.get_continental_risk(regions)
        continental_event_projection_runtime.project_risk_updated(
            continent=continent,
            risk_level=risk_report["risk_level"],
            risk_index=risk_report["continental_risk_index"],
        )
        continental_state_runtime.update_continental_state(
            {"continents": {continent: {"risk_level": risk_report["risk_level"]}}}
        )
        self._audit("CONTINENTAL_RISK_UPDATED", {"continent": continent, **risk_report})
        return {**risk_report, "continent": continent}

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def take_snapshot(self, continent: Optional[str] = None) -> Dict[str, Any]:
        state_snap = continental_state_runtime.get_snapshot()
        fed_status = continental_federation_runtime.status()
        dep_status = continental_dependency_runtime.status()
        proj_status = continental_event_projection_runtime.status()

        snapshot = {
            "snapshot_id": str(uuid4()),
            "scope": "CONTINENTAL",
            "continent": continent,
            "state": state_snap,
            "federation": fed_status,
            "dependencies": dep_status,
            "projections": proj_status,
            "audit_log_size": len(self._audit_log),
            "decisions_count": len(self._decisions),
            "captured_at": self._utc_now(),
        }

        if continent:
            continental_event_projection_runtime.project_state_snapshot(continent=continent, snapshot=state_snap)

        self._audit("CONTINENTAL_STATE_SNAPSHOT", {"snapshot_id": snapshot["snapshot_id"]})
        return snapshot

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _audit(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._audit_log.append(
            {
                "audit_id": str(uuid4()),
                "event_type": event_type,
                "payload": deepcopy(payload),
                "recorded_at": self._utc_now(),
            }
        )

    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self._audit_log[-limit:] if limit else self._audit_log
        return deepcopy(data)

    def get_decisions(self, continent: Optional[str] = None) -> List[Dict[str, Any]]:
        if continent:
            return [deepcopy(d) for d in self._decisions if d["continent"] == continent]
        return [deepcopy(d) for d in self._decisions]

    def list_policies(self, continent: Optional[str] = None) -> List[Dict[str, Any]]:
        policies = self._policies.values()
        if continent:
            policies = (p for p in policies if p["continent"] == continent)
        return [deepcopy(p) for p in policies]

    def status(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "policies_registered": len(self._policies),
            "decisions_created": len(self._decisions),
            "audit_log_size": len(self._audit_log),
        }


continental_governance_runtime = ContinentalGovernanceRuntime()


def run_continental_layer_demo() -> Dict[str, Any]:
    """Demonstração do primeiro fluxo da camada continental."""
    gov = continental_governance_runtime

    # Inicializa estado base
    continental_state_runtime.initialize()
    continental_event_projection_runtime.initialize()

    # Cria continentes
    africa = gov.create_continent("AFRICA", {"hemisphere": "south_north"})
    europe = gov.create_continent("EUROPE", {"hemisphere": "north"})
    asia = gov.create_continent("ASIA", {"hemisphere": "north"})

    # Registra regiões
    gov.register_region("AFRICA", "sub-saharan", "earth-runtime-af-001")
    gov.register_region("EUROPE", "western-europe", "earth-runtime-eu-001")
    gov.register_region("ASIA", "east-asia", "earth-runtime-as-001")

    # Detecta dependências
    continental_dependency_runtime.register_dependency(
        source_region="western-europe",
        target_region="east-asia",
        dependency_type="SUPPLY_CHAIN",
        strength=0.85,
        continent="EUROPE",
    )
    continental_event_projection_runtime.project_dependency_detected(
        source_region="western-europe",
        target_region="east-asia",
        dependency_type="SUPPLY_CHAIN",
    )

    # Atualiza risco
    continental_dependency_runtime.update_risk("western-europe", 0.25)
    continental_dependency_runtime.update_risk("east-asia", 0.3)
    gov.evaluate_risk("EUROPE", ["western-europe"])

    # Propaga evento continental
    continental_federation_runtime.propagate_continental_event(
        event_type="CONTINENTAL_RISK_UPDATED",
        origin_continent="EUROPE",
        target_continents=["ASIA", "AFRICA"],
    )

    # Decisão de governança
    gov.create_decision(
        continent="EUROPE",
        decision_type="RISK_MITIGATION",
        rationale="Risco moderado detectado em western-europe; iniciar protocolo de mitigação.",
    )

    # Snapshot final
    snapshot = gov.take_snapshot(continent="EUROPE")

    return {
        "continents_created": [africa, europe, asia],
        "final_snapshot": snapshot,
        "federation_status": continental_federation_runtime.status(),
        "state_checksum": continental_state_runtime.current_checksum(),
    }

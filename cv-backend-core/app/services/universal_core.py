from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


DEFAULT_PHASES = ["ideia", "viabilidade", "aprovacao", "execucao", "encerramento"]
DEFAULT_EVENT_CATALOG = ["project.created", "project.approved", "project.started", "project.closed"]


class UniversalCoreService:
    def __init__(self, bus: Any) -> None:
        self.bus = bus
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.sequences: Dict[str, int] = {}
        self.phases: List[str] = list(DEFAULT_PHASES)
        self.phase_rules: Dict[str, List[str]] = {phase: [] for phase in self.phases}
        self.event_catalog: List[str] = list(DEFAULT_EVENT_CATALOG)
        self.signals: List[Dict[str, Any]] = []
        self.scenarios: List[str] = ["expansion", "stability", "contraction", "stress"]
        self.audit_events: List[Dict[str, Any]] = []
        self.thresholds: Dict[str, float] = {"healthy_min": 80.0, "attention_min": 60.0}
        self.health_scores: List[Dict[str, Any]] = []
        self.knowledge_bank: List[Dict[str, Any]] = []
        self.decision_history: List[Dict[str, Any]] = []
        self.john_history: List[Dict[str, Any]] = []

    def create_project(
        self,
        *,
        portfolio: str,
        program: str,
        project: str,
        tenant: str,
        project_type: str = "PRJ",
        year: int | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not portfolio or not program or not project:
            raise ValueError("missing_pyramid_fields")

        resolved_year = int(year or datetime.now(timezone.utc).year)
        mother_code = self._next_mother_code(
            portfolio=portfolio,
            program=program,
            project_type=project_type,
            year=resolved_year,
        )

        project_id = str(uuid.uuid4())
        payload = {
            "id": project_id,
            "tenant": tenant,
            "pyramid": {
                "portfolio": portfolio,
                "program": program,
                "project": project,
            },
            "mother_code": mother_code,
            "project_type": project_type,
            "year": resolved_year,
            "metadata": self._normalize_metadata(metadata),
            "governance": {
                "current_phase": self.phases[0],
                "history": [
                    {
                        "phase": self.phases[0],
                        "action": "created",
                        "at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.projects[project_id] = payload

        self.publish_event(
            event_type="project.created",
            source="universal.core",
            tenant=tenant,
            payload={
                "project_id": project_id,
                "mother_code": mother_code,
                "pyramid": payload["pyramid"],
            },
        )

        return payload

    def get_project(self, project_id: str) -> Dict[str, Any]:
        project = self.projects.get(project_id)
        if project is None:
            raise KeyError("project_not_found")
        return project

    def get_project_scoped(self, project_id: str, tenant: str, role: str = "") -> Dict[str, Any]:
        project = self.get_project(project_id)
        normalized_role = str(role or "").upper()
        if normalized_role != "ADMIN" and str(project.get("tenant", "")) != str(tenant):
            raise PermissionError("tenant_scope_violation")
        return project

    def configure_phases(self, phases: List[str]) -> Dict[str, Any]:
        normalized = [str(item).strip().lower() for item in phases if str(item).strip()]
        if len(normalized) < 2:
            raise ValueError("invalid_phases")
        self.phases = normalized
        self.phase_rules = {phase: list(self.phase_rules.get(phase, [])) for phase in self.phases}
        return {"phases": list(self.phases)}

    def add_phase_rule(self, phase: str, rule: str) -> Dict[str, Any]:
        normalized_phase = str(phase).strip().lower()
        normalized_rule = str(rule).strip()
        if normalized_phase not in self.phases:
            raise ValueError("phase_not_configured")
        if not normalized_rule:
            raise ValueError("invalid_rule")
        self.phase_rules.setdefault(normalized_phase, [])
        self.phase_rules[normalized_phase].append(normalized_rule)
        return {"phase": normalized_phase, "rules": list(self.phase_rules[normalized_phase])}

    def advance_workflow(
        self,
        project_id: str,
        metrics: Dict[str, Any] | None = None,
        actor: str = "system",
        tenant: str = "",
        role: str = "",
    ) -> Dict[str, Any]:
        project = self.get_project_scoped(project_id, tenant=tenant, role=role)
        current_phase = str(project["governance"]["current_phase"])
        if current_phase not in self.phases:
            project["governance"]["current_phase"] = self.phases[0]
            current_phase = self.phases[0]

        current_index = self.phases.index(current_phase)
        if current_index >= len(self.phases) - 1:
            return {
                "status": "final_phase_reached",
                "project_id": project_id,
                "phase": current_phase,
            }

        checks = self._validate_rules(current_phase, metrics or {})
        if not checks["ok"]:
            history_entry = {
                "phase": current_phase,
                "action": "validation_failed",
                "at": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "details": checks,
            }
            project["governance"]["history"].append(history_entry)
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            return {
                "status": "blocked",
                "project_id": project_id,
                "phase": current_phase,
                "validation": checks,
            }

        next_phase = self.phases[current_index + 1]
        history_entry = {
            "phase": next_phase,
            "action": "transition",
            "from": current_phase,
            "to": next_phase,
            "at": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "validation": checks,
        }
        project["governance"]["current_phase"] = next_phase
        project["governance"]["history"].append(history_entry)
        project["updated_at"] = datetime.now(timezone.utc).isoformat()

        event_type = self._event_for_phase(next_phase)
        self.publish_event(
            event_type=event_type,
            source="universal.workflow",
            tenant=str(project["tenant"]),
            payload={
                "project_id": project_id,
                "from": current_phase,
                "to": next_phase,
                "mother_code": project["mother_code"],
            },
        )

        return {
            "status": "advanced",
            "project_id": project_id,
            "phase": next_phase,
            "history_size": len(project["governance"]["history"]),
            "validation": checks,
            "event_type": event_type,
        }

    def score_decision(
        self,
        *,
        retorno: float,
        risco: float,
        demanda: float,
        tenant: str = "tenant_liceu",
        weights: Dict[str, float] | None = None,
    ) -> Dict[str, Any]:
        cfg = {
            "retorno": 0.5,
            "risco": 0.3,
            "demanda": 0.2,
        }
        cfg.update(weights or {})
        score = (retorno * cfg["retorno"]) - (risco * cfg["risco"]) + (demanda * cfg["demanda"])
        scaled = round(max(0.0, min(100.0, score)), 2)
        decision = "APPROVED" if scaled >= 70 else "REVIEW"
        result = {
            "score": scaled,
            "decision": decision,
            "weights": cfg,
            "formula": "(retorno * peso1) - (risco * peso2) + (demanda * peso3)",
        }
        self.decision_history.insert(
            0,
            {
                **result,
                "retorno": retorno,
                "risco": risco,
                "demanda": demanda,
                "tenant": str(tenant),
                "at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.decision_history = self.decision_history[:500]
        return result

    def ingest_signal(self, *, source: str, signal_type: str, value: float, tenant: str) -> Dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "source": str(source),
            "type": str(signal_type),
            "value": float(value),
            "tenant": str(tenant),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.signals.insert(0, item)
        self.signals = self.signals[:1000]
        self.publish_event(
            event_type="macro.ingested",
            source="universal.econotech",
            tenant=tenant,
            payload={"signal_id": item["id"], "type": item["type"], "value": item["value"]},
        )
        return item

    def list_signals(self, *, signal_type: str = "", tenant: str = "", limit: int = 20) -> Dict[str, Any]:
        items = list(self.signals)
        if signal_type:
            items = [item for item in items if item["type"] == signal_type]
        if tenant:
            items = [item for item in items if item["tenant"] == tenant]
        bounded = max(1, min(int(limit or 20), 200))
        return {"items": items[:bounded], "count": len(items[:bounded])}

    def configure_scenarios(self, names: List[str]) -> Dict[str, Any]:
        normalized = [str(item).strip().lower() for item in names if str(item).strip()]
        if len(normalized) < 2:
            raise ValueError("invalid_scenarios")
        self.scenarios = normalized
        return {"scenarios": list(self.scenarios)}

    def impact_adapter(self, *, project_id: str, scenario: str, tenant: str = "", role: str = "") -> Dict[str, Any]:
        project = self.get_project_scoped(project_id, tenant=tenant, role=role)
        normalized_scenario = str(scenario).strip().lower()
        if normalized_scenario not in self.scenarios:
            raise ValueError("scenario_not_configured")

        latest_interest = self._latest_signal_value("interest_rate", tenant=tenant or str(project["tenant"]), fallback=10.0)
        latest_inflation = self._latest_signal_value("inflation", tenant=tenant or str(project["tenant"]), fallback=4.0)
        latest_demand = self._latest_signal_value("demand", tenant=tenant or str(project["tenant"]), fallback=70.0)

        multiplier = {
            "expansion": 0.85,
            "stability": 1.0,
            "contraction": 1.2,
            "stress": 1.45,
        }.get(normalized_scenario, 1.0)

        risk_pressure = round(((latest_interest * 2.0) + latest_inflation - (latest_demand * 0.3)) * multiplier, 2)
        impact_score = round(max(0.0, min(100.0, 100.0 - risk_pressure)), 2)
        action = "maintain"
        if impact_score < 45:
            action = "pause"
        elif impact_score < 70:
            action = "adjust"
        elif impact_score >= 85:
            action = "accelerate"

        result = {
            "project_id": project_id,
            "mother_code": project["mother_code"],
            "scenario": normalized_scenario,
            "drivers": {
                "interest_rate": latest_interest,
                "inflation": latest_inflation,
                "demand": latest_demand,
            },
            "risk_pressure": risk_pressure,
            "impact_score": impact_score,
            "recommended_action": action,
        }
        self.publish_event(
            event_type="project.impact.assessed",
            source="universal.econotech",
            tenant=str(project["tenant"]),
            payload=result,
        )
        return result

    def ingest_audit(self, *, source: str, entity: str, severity: str, action: str, tenant: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        normalized_severity = str(severity or "").upper()
        if normalized_severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            normalized_severity = "MEDIUM"
        item = {
            "id": str(uuid.uuid4()),
            "source": str(source),
            "entity": str(entity),
            "severity": normalized_severity,
            "action": str(action),
            "tenant": str(tenant),
            "context": dict(context or {}),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_events.insert(0, item)
        self.audit_events = self.audit_events[:1000]

        recurrence = self._audit_recurrence(item)
        structural = recurrence >= 3
        auto_actions = self._audit_auto_actions(item, structural)
        result = {
            **item,
            "recurrence": recurrence,
            "structural": structural,
            "automatic_actions": auto_actions,
        }

        self.publish_event(
            event_type="audit.detected",
            source="universal.audit",
            tenant=tenant,
            payload={
                "audit_id": item["id"],
                "entity": item["entity"],
                "severity": item["severity"],
                "recurrence": recurrence,
                "structural": structural,
            },
        )
        return result

    def audit_summary(self, *, tenant: str = "") -> Dict[str, Any]:
        items = list(self.audit_events)
        if tenant:
            items = [item for item in items if item["tenant"] == tenant]

        severity_counts: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for item in items:
            severity_counts[item["severity"]] = severity_counts.get(item["severity"], 0) + 1
        structural_count = 0
        for item in items:
            if self._audit_recurrence(item) >= 3:
                structural_count += 1

        return {
            "count": len(items),
            "severity": severity_counts,
            "structural_count": structural_count,
            "items": items[:50],
        }

    def compute_health_score(self, *, finance: float, operational: float, risk: float, tenant: str) -> Dict[str, Any]:
        normalized = {
            "finance": float(finance),
            "operational": float(operational),
            "risk": float(risk),
        }
        overall = round((normalized["finance"] + normalized["operational"] + normalized["risk"]) / 3.0, 2)
        status = "saudavel"
        if overall < self.thresholds["attention_min"]:
            status = "critico"
        elif overall < self.thresholds["healthy_min"]:
            status = "atencao"

        payload = {
            "id": str(uuid.uuid4()),
            "tenant": tenant,
            "dimensions": normalized,
            "overall": overall,
            "status": status,
            "thresholds": dict(self.thresholds),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.health_scores.insert(0, payload)
        self.health_scores = self.health_scores[:500]

        self.publish_event(
            event_type="health.updated",
            source="universal.hospital",
            tenant=tenant,
            payload={
                "health_id": payload["id"],
                "overall": overall,
                "status": status,
            },
        )
        return payload

    def configure_thresholds(self, *, healthy_min: float, attention_min: float) -> Dict[str, Any]:
        if attention_min >= healthy_min:
            raise ValueError("invalid_thresholds")
        self.thresholds = {
            "healthy_min": float(healthy_min),
            "attention_min": float(attention_min),
        }
        return {"thresholds": dict(self.thresholds)}

    def john_interpret(self, *, data: Dict[str, Any], scenario: str, score: float, tenant: str) -> Dict[str, Any]:
        action = self.john_decision_mode(score=score)
        summary = (
            f"No cenario {scenario}, score {round(float(score), 2)} sugere {action}. "
            f"Dados-chave: {', '.join(sorted([str(k) for k in data.keys()])[:4]) or 'n/a'}."
        )
        result = {
            "recommendation": summary,
            "mode": action,
            "score": round(float(score), 2),
            "scenario": scenario,
        }
        self.john_history.insert(0, {**result, "tenant": tenant, "at": datetime.now(timezone.utc).isoformat()})
        self.john_history = self.john_history[:500]
        self.publish_event(
            event_type="john.interpreted",
            source="universal.john",
            tenant=tenant,
            payload=result,
        )
        return result

    def john_decision_mode(self, *, score: float) -> str:
        numeric = float(score)
        if numeric >= 80:
            return "acelerar"
        if numeric >= 60:
            return "manter"
        return "pausar"

    def record_knowledge(self, *, input_data: Dict[str, Any], resultado: Dict[str, Any], licao: str, tenant: str) -> Dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "tenant": tenant,
            "input": dict(input_data or {}),
            "resultado": dict(resultado or {}),
            "licao": str(licao or "").strip(),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.knowledge_bank.insert(0, item)
        self.knowledge_bank = self.knowledge_bank[:1000]
        self.publish_event(
            event_type="knowledge.recorded",
            source="universal.knowledge",
            tenant=tenant,
            payload={"knowledge_id": item["id"]},
        )
        return item

    def reuse_knowledge(self, *, input_data: Dict[str, Any], tenant: str, limit: int = 5) -> Dict[str, Any]:
        keys = set(str(key) for key in (input_data or {}).keys())
        scored: List[Dict[str, Any]] = []
        for item in self.knowledge_bank:
            if tenant and item["tenant"] != tenant:
                continue
            overlap = len(keys.intersection(set(item["input"].keys())))
            scored.append({"overlap": overlap, "item": item})
        scored.sort(key=lambda row: row["overlap"], reverse=True)
        bounded = max(1, min(int(limit or 5), 20))
        selected = [row["item"] for row in scored[:bounded] if row["overlap"] > 0]
        return {"count": len(selected), "items": selected}

    def dashboard_snapshot(self, *, tenant: str) -> Dict[str, Any]:
        projects = [item for item in self.projects.values() if item["tenant"] == tenant]
        audits = [item for item in self.audit_events if item["tenant"] == tenant]
        latest_health = next((item for item in self.health_scores if item["tenant"] == tenant), None)
        latest_decision = next((item for item in self.decision_history if item.get("tenant") == tenant), None)
        latest_john = next((item for item in self.john_history if item["tenant"] == tenant), None)

        alerts: List[str] = []
        if latest_health and latest_health["status"] != "saudavel":
            alerts.append("risco ↑")
        if latest_decision and latest_decision["score"] < 70:
            alerts.append("score ↓")
        if any(item["severity"] in {"HIGH", "CRITICAL"} for item in audits[:10]):
            alerts.append("risco operacional ↑")

        return {
            "status": latest_health["status"] if latest_health else "n/a",
            "risco": latest_health["dimensions"]["risk"] if latest_health else None,
            "financeiro": latest_health["dimensions"]["finance"] if latest_health else None,
            "decision": latest_decision["decision"] if latest_decision else "n/a",
            "john": latest_john["recommendation"] if latest_john else "n/a",
            "alerts": alerts,
            "kpis": {
                "projects": len(projects),
                "audits": len(audits),
                "knowledge_items": len([item for item in self.knowledge_bank if item["tenant"] == tenant]),
            },
        }

    def publish_event(self, *, event_type: str, source: str, tenant: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        envelope = {
            "id": str(uuid.uuid4()),
            "type": str(event_type),
            "source": str(source),
            "tenant": str(tenant or "tenant_liceu"),
            "payload": dict(payload or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        channel = str(event_type)
        result = self.bus.publish(channel, envelope)
        return {
            "envelope": envelope,
            "channel": channel,
            "provider": result.provider,
            "delivered": result.delivered,
        }

    def simulate_events(self, *, tenant: str, event_types: List[str], seed_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        emitted: List[Dict[str, Any]] = []
        for event_type in event_types:
            emitted.append(
                self.publish_event(
                    event_type=event_type,
                    source="universal.simulator",
                    tenant=tenant,
                    payload={
                        "simulated": True,
                        **(seed_payload or {}),
                    },
                )
            )
        return {"count": len(emitted), "events": emitted}

    def events_catalog(self) -> Dict[str, Any]:
        return {
            "events": list(
                set(
                    self.event_catalog
                    + [
                        "project.updated",
                        "macro.ingested",
                        "project.impact.assessed",
                        "audit.detected",
                        "health.updated",
                        "john.interpreted",
                        "knowledge.recorded",
                    ]
                )
            ),
            "envelope": {
                "id": "",
                "type": "",
                "source": "",
                "tenant": "",
                "payload": {},
            },
        }

    def _next_mother_code(self, *, portfolio: str, program: str, project_type: str, year: int) -> str:
        portfolio_code = self._token(portfolio)
        program_code = self._token(program)
        type_code = self._token(project_type)
        key = f"{portfolio_code}-{program_code}-{type_code}-{year}"
        next_seq = self.sequences.get(key, 0) + 1
        self.sequences[key] = next_seq
        return f"{key}-{next_seq:03d}"

    def _normalize_metadata(self, metadata: Dict[str, Any] | None) -> Dict[str, Any]:
        incoming = dict(metadata or {})
        return {
            "area": incoming.get("area", 0),
            "tipologia": incoming.get("tipologia", ""),
            "unidades": incoming.get("unidades", 0),
            "custom_fields": incoming.get("custom_fields", {}),
        }

    def _token(self, raw: str) -> str:
        text = re.sub(r"[^A-Za-z0-9]+", "", str(raw or "").upper())
        if len(text) >= 3:
            return text[:3]
        return (text + "XXX")[:3]

    def _validate_rules(self, phase: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        rules = list(self.phase_rules.get(phase, []))
        if not rules:
            return {"ok": True, "rules": [], "failed": []}

        failed = []
        for rule in rules:
            if not self._evaluate_expression(rule, metrics):
                failed.append(rule)
        return {
            "ok": len(failed) == 0,
            "rules": rules,
            "failed": failed,
        }

    def _evaluate_expression(self, expression: str, metrics: Dict[str, Any]) -> bool:
        pattern = r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(>=|<=|>|<|==|!=)\s*([0-9]+(?:\.[0-9]+)?)(%?)\s*$"
        match = re.match(pattern, expression or "")
        if match is None:
            return False

        field_name, operator, raw_value, is_percent = match.groups()
        left = float(metrics.get(field_name, 0) or 0)
        right = float(raw_value)
        if is_percent:
            right = right

        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        return False

    def _event_for_phase(self, phase: str) -> str:
        normalized = str(phase or "").lower()
        if "aprov" in normalized:
            return "project.approved"
        if "exec" in normalized:
            return "project.started"
        if "encerr" in normalized or normalized == self.phases[-1]:
            return "project.closed"
        return "project.updated"

    def _latest_signal_value(self, signal_type: str, *, tenant: str, fallback: float) -> float:
        for item in self.signals:
            if item["type"] == signal_type and item["tenant"] == tenant:
                return float(item["value"])
        return fallback

    def _audit_recurrence(self, item: Dict[str, Any]) -> int:
        count = 0
        for row in self.audit_events:
            if row["tenant"] == item["tenant"] and row["entity"] == item["entity"] and row["action"] == item["action"]:
                count += 1
        return count

    def _audit_auto_actions(self, item: Dict[str, Any], structural: bool) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        if item["severity"] in {"HIGH", "CRITICAL"}:
            actions.append({"type": "task", "description": f"mitigar incidente em {item['entity']}"})
        if structural:
            actions.append({"type": "treinamento", "description": "treinamento de recorrencia estrutural"})
            actions.append({"type": "ajuste_de_processo", "description": "revisar fluxo para eliminar recorrencia"})
        return actions
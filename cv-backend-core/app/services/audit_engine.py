from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.immutable_audit_service import ImmutableAuditService
from app.services.risk_flag_service import RiskFlagService
from app.models.orchestration import AuditAction, AuditEvent, AuditLog


SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass
class NormalizedAuditEvent:
    source: str
    entity_id: str | None
    entity_type: str
    event_type: str
    audit_domain: str
    severity: str
    description: str
    payload: dict[str, Any]
    detected_at: datetime


class AuditEngine:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        source: str = "core_os",
        detected_at: datetime | None = None,
    ) -> AuditEvent:
        normalized = self.normalize_event(event_type, payload, source=source, detected_at=detected_at)
        event = AuditEvent(
            source=normalized.source,
            entity_id=normalized.entity_id,
            entity_type=normalized.entity_type,
            event_type=normalized.event_type,
            audit_domain=normalized.audit_domain,
            severity=normalized.severity,
            description=normalized.description,
            payload=normalized.payload,
            detected_at=normalized.detected_at,
        )
        self.db.add(event)
        self.db.flush()
        generated_actions = self._create_actions_for_event(event)
        self.db.add(
            AuditLog(
                user_id=None,
                action=f"audit.event.ingested.{normalized.severity.lower()}",
                entity_type="audit_event",
                entity_id=event.id,
            )
        )
        for action in generated_actions:
            self.db.add(
                AuditLog(
                    user_id=None,
                    action=f"audit.action.generated.{action.action_type}",
                    entity_type="audit_action",
                    entity_id=action.id,
                )
            )
        immutable = ImmutableAuditService(self.db)
        immutable.append(
            entity_type="audit_event",
            entity_id=event.id,
            action=f"audit.event.ingested.{normalized.severity.lower()}",
            actor="audit_engine",
            payload={
                "event_type": event.event_type,
                "source": event.source,
                "severity": event.severity,
                "audit_domain": event.audit_domain,
            },
        )
        for action in generated_actions:
            immutable.append(
                entity_type="audit_action",
                entity_id=action.id,
                action=f"audit.action.generated.{action.action_type}",
                actor="audit_engine",
                payload={
                    "audit_id": action.audit_id,
                    "status": action.status,
                    "assigned_to": action.assigned_to,
                },
            )
        self.db.commit()
        # Verificar se o evento aciona alguma flag de risco (pós-commit para evitar deadlock de flush)
        try:
            RiskFlagService(self.db).detect_from_event(event)
            self.db.commit()
        except Exception:
            pass
        self.db.refresh(event)
        return event

    def list_events(
        self,
        *,
        limit: int = 100,
        source: str | None = None,
        severity: str | None = None,
        audit_domain: str | None = None,
    ) -> list[AuditEvent]:
        query = self.db.query(AuditEvent)
        if source:
            query = query.filter(AuditEvent.source == source)
        if severity:
            query = query.filter(AuditEvent.severity == severity.upper())
        if audit_domain:
            query = query.filter(AuditEvent.audit_domain == audit_domain)
        return query.order_by(AuditEvent.detected_at.desc()).limit(limit).all()

    def list_actions(
        self,
        *,
        limit: int = 100,
        action_type: str | None = None,
        status: str | None = None,
    ) -> list[AuditAction]:
        query = self.db.query(AuditAction)
        if action_type:
            query = query.filter(AuditAction.action_type == action_type)
        if status:
            query = query.filter(AuditAction.status == status)
        return query.order_by(AuditAction.created_at.desc()).limit(limit).all()

    def normalize_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        source: str,
        detected_at: datetime | None,
    ) -> NormalizedAuditEvent:
        normalized_type = (event_type or "unknown.event").strip().lower()
        normalized_source = (source or "core_os").strip().lower().replace("-", "_")
        entity_id = self._resolve_entity_id(payload)
        entity_type = self._resolve_entity_type(payload, normalized_type)
        audit_domain = self._resolve_domain(normalized_source, normalized_type)
        severity = self._resolve_severity(normalized_source, normalized_type, payload, entity_id)
        recurrence_count = self._resolve_recurrence_count(normalized_source, normalized_type, entity_id)
        normalized_payload = dict(payload or {})
        normalized_payload["audit_context"] = {
            "recurrence_count": recurrence_count,
            "normalized_source": normalized_source,
            "audit_domain": audit_domain,
        }
        description = self._build_description(normalized_source, normalized_type, audit_domain, severity, normalized_payload)

        return NormalizedAuditEvent(
            source=normalized_source,
            entity_id=entity_id,
            entity_type=entity_type,
            event_type=normalized_type,
            audit_domain=audit_domain,
            severity=severity,
            description=description,
            payload=normalized_payload,
            detected_at=detected_at or datetime.now(timezone.utc),
        )

    def _resolve_entity_id(self, payload: dict[str, Any]) -> str | None:
        for field in ["entity_id", "project_id", "work_id", "task_id", "plan_id", "initiative_id", "card_id", "supplier_id", "company_id"]:
            value = payload.get(field)
            if value is not None:
                return str(value)
        return None

    def _resolve_entity_type(self, payload: dict[str, Any], event_type: str) -> str:
        explicit = payload.get("entity_type")
        if explicit:
            return str(explicit)
        if "." in event_type:
            return event_type.split(".", 1)[0]
        return "generic"

    def _resolve_domain(self, source: str, event_type: str) -> str:
        searchable = f"{source} {event_type}"
        if any(token in searchable for token in ["hub", "cea", "payment", "invoice", "cashflow", "budget"]):
            return "financial"
        if any(token in searchable for token in ["jurid", "compliance", "bypass", "contract", "fraud"]):
            return "compliance"
        if any(token in searchable for token in ["pdi", "pd", "process", "workflow"]):
            return "process"
        if any(token in searchable for token in ["code", "deploy", "runtime", "system", "tech"]):
            return "technology"
        if any(token in searchable for token in ["sale", "lead", "deal", "proposal", "commercial"]):
            return "commercial"
        if any(token in searchable for token in ["supplier", "vendor", "delivery", "fornecedor"]):
            return "suppliers"
        return "operations"

    def _resolve_severity(self, source: str, event_type: str, payload: dict[str, Any], entity_id: str | None) -> str:
        payload_risk = str(payload.get("risk") or payload.get("risk_level") or "").strip().lower()
        severity = "LOW"
        if payload.get("blocking") is True or payload.get("blocked") is True:
            severity = "CRITICAL"
        elif payload_risk in {"critical", "crítico"}:
            severity = "CRITICAL"
        elif any(token in event_type for token in ["bypass.detected", "fraud", "violation", "outage", "breach"]):
            severity = "CRITICAL"
        elif payload_risk == "high":
            severity = "HIGH"
        elif any(token in event_type for token in ["overdue", "delay", "blocked", "pending", "warning"]):
            severity = "HIGH"
        elif payload_risk == "medium":
            severity = "MEDIUM"
        elif any(token in event_type for token in ["required", "review", "drift", "deviation"]):
            severity = "MEDIUM"

        recurrence_count = self._resolve_recurrence_count(source, event_type, entity_id)
        if recurrence_count >= 1:
            severity = self._escalate_severity(severity)
        if recurrence_count >= 3:
            severity = self._escalate_severity(severity)
        return severity

    def _resolve_recurrence_count(self, source: str, event_type: str, entity_id: str | None) -> int:
        query = self.db.query(AuditEvent).filter(
            AuditEvent.source == source,
            AuditEvent.event_type == event_type,
            AuditEvent.detected_at >= datetime.now(timezone.utc) - timedelta(days=30),
        )
        if entity_id is not None:
            query = query.filter(AuditEvent.entity_id == entity_id)
        return query.count()

    def _escalate_severity(self, severity: str) -> str:
        ordered = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        try:
            index = ordered.index(severity)
        except ValueError:
            return "MEDIUM"
        return ordered[min(index + 1, len(ordered) - 1)]

    def _build_description(
        self,
        source: str,
        event_type: str,
        audit_domain: str,
        severity: str,
        payload: dict[str, Any],
    ) -> str:
        title = str(payload.get("title") or payload.get("name") or payload.get("description") or "").strip()
        recurrence_count = int(((payload.get("audit_context") or {}).get("recurrence_count") or 0))
        if title:
            recurrence_note = f" com recorrencia {recurrence_count}" if recurrence_count > 0 else ""
            return f"{audit_domain}::{severity.lower()} detectado em {source} para '{title}' via {event_type}{recurrence_note}"
        return f"{audit_domain}::{severity.lower()} detectado em {source} via {event_type}"

    def _create_actions_for_event(self, event: AuditEvent) -> list[AuditAction]:
        actions: list[AuditAction] = []
        audit_context = (event.payload or {}).get("audit_context") or {}
        recurrence_count = int(audit_context.get("recurrence_count") or 0)
        owner = (event.payload or {}).get("owner") or (event.payload or {}).get("assigned_to")

        if event.severity in {"MEDIUM", "HIGH", "CRITICAL"}:
            actions.append(
                AuditAction(
                    audit_id=event.id,
                    action_type="task",
                    assigned_to=str(owner or "governance_ops"),
                    status="pending",
                    details={
                        "summary": event.description,
                        "severity": event.severity,
                        "audit_domain": event.audit_domain,
                    },
                )
            )

        if recurrence_count >= 2 or event.severity in {"HIGH", "CRITICAL"}:
            actions.append(
                AuditAction(
                    audit_id=event.id,
                    action_type="training",
                    assigned_to="academia_saber",
                    status="pending",
                    details={
                        "journey_name": f"Correcao {event.audit_domain} • {event.event_type}",
                        "reason": event.description,
                        "mandatory": event.severity in {"HIGH", "CRITICAL"},
                    },
                )
            )

        if event.audit_domain in {"process", "operations", "compliance"} and (recurrence_count >= 1 or event.severity == "CRITICAL"):
            actions.append(
                AuditAction(
                    audit_id=event.id,
                    action_type="process_update",
                    assigned_to="pdi_ia",
                    status="pending",
                    details={
                        "reason": event.description,
                        "event_type": event.event_type,
                        "recurrence_count": recurrence_count,
                    },
                )
            )

        for action in actions:
            self.db.add(action)
        self.db.flush()
        return actions


def serialize_audit_event(event: AuditEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "source": event.source,
        "entity_id": event.entity_id,
        "entity_type": event.entity_type,
        "event_type": event.event_type,
        "audit_domain": event.audit_domain,
        "severity": event.severity,
        "description": event.description,
        "payload": event.payload or {},
        "detected_at": event.detected_at.isoformat() if event.detected_at else None,
    }


def serialize_audit_action(action: AuditAction) -> dict[str, Any]:
    return {
        "id": action.id,
        "audit_id": action.audit_id,
        "action_type": action.action_type,
        "assigned_to": action.assigned_to,
        "status": action.status,
        "details": action.details or {},
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }
"""
Risk Flag Service — #210
Detecta, persiste e resolve flags de risco (fraude, inadimplência, inconsistência)
com base em AuditEvents, integrando à trilha imutável.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.orchestration import AuditEvent, RiskFlag
from app.services.immutable_audit_service import ImmutableAuditService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento de event_type → flag_type + severidade padrão
# ---------------------------------------------------------------------------
_FLAG_RULES: list[dict[str, Any]] = [
    # Fraude
    {"keywords": ["fraud", "fraude", "suspicious", "suspeita"], "flag_type": "fraud", "severity": "critical"},
    # Inadimplência
    {"keywords": ["debt", "default", "inadimpl", "overdue", "atraso"], "flag_type": "default", "severity": "high"},
    # Inconsistência
    {"keywords": ["inconsist", "mismatch", "divergen", "conflict", "erro_dado"], "flag_type": "inconsistency", "severity": "medium"},
]

_SEVERITY_FROM_EVENT: dict[str, str] = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def _detect_flag_type_and_severity(event: AuditEvent) -> tuple[str, str] | None:
    """Retorna (flag_type, severity) ou None se o evento não aciona nenhuma flag."""
    event_key = (event.event_type or "").lower()
    for rule in _FLAG_RULES:
        if any(kw in event_key for kw in rule["keywords"]):
            # Usa severidade do evento se disponível, senão a do mapeamento
            sev = _SEVERITY_FROM_EVENT.get(event.severity or "", rule["severity"])
            return rule["flag_type"], sev
    return None


def serialize_risk_flag(flag: RiskFlag) -> dict[str, Any]:
    return {
        "id": flag.id,
        "company_id": flag.company_id,
        "flag_type": flag.flag_type,
        "severity": flag.severity,
        "status": flag.status,
        "source_entity_type": flag.source_entity_type,
        "source_entity_id": flag.source_entity_id,
        "description": flag.description,
        "detected_at": flag.detected_at.isoformat() if flag.detected_at else None,
        "resolved_at": flag.resolved_at.isoformat() if flag.resolved_at else None,
        "resolved_by": flag.resolved_by,
        "resolution_notes": flag.resolution_notes,
        "context": flag.context or {},
    }


class RiskFlagService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Detecção automática a partir de um AuditEvent
    # ------------------------------------------------------------------

    def detect_from_event(self, event: AuditEvent) -> RiskFlag | None:
        """Analisa um AuditEvent e cria uma RiskFlag se aplicável."""
        result = _detect_flag_type_and_severity(event)
        if result is None:
            return None

        flag_type, severity = result

        flag = RiskFlag(
            company_id=event.entity_id or event.source or "unknown",
            flag_type=flag_type,
            severity=severity,
            status="active",
            source_entity_type="audit_event",
            source_entity_id=event.id,
            description=f"Flag detectada automaticamente: {flag_type} — {event.event_type}",
            context={
                "event_type": event.event_type,
                "event_severity": event.severity,
                "source": event.source,
            },
        )
        self.db.add(flag)
        self.db.flush()

        # Registrar detecção na trilha imutável
        ImmutableAuditService(self.db).append(
            entity_type="risk_flag",
            entity_id=flag.id,
            action=f"risk.flag.detected.{flag_type}",
            actor="system",
            payload={
                "flag_type": flag_type,
                "severity": severity,
                "company_id": flag.company_id,
                "source_event_id": event.id,
            },
        )

        logger.info("RiskFlag criada: %s / %s / company=%s", flag.id, flag_type, flag.company_id)
        return flag

    # ------------------------------------------------------------------
    # Detecção em lote para uma empresa (re-analisa eventos não processados)
    # ------------------------------------------------------------------

    def detect_for_company(self, company_id: str) -> list[RiskFlag]:
        """Analisa eventos recentes da empresa e gera flags para os que ainda não têm flag."""
        existing_event_ids: set[str] = {
            f.source_entity_id
            for f in self.db.query(RiskFlag)
            .filter(RiskFlag.company_id == company_id, RiskFlag.source_entity_type == "audit_event")
            .all()
        }

        events = (
            self.db.query(AuditEvent)
            .filter(AuditEvent.entity_id == company_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
            .all()
        )

        created: list[RiskFlag] = []
        for event in events:
            if event.id in existing_event_ids:
                continue
            flag = self.detect_from_event(event)
            if flag:
                created.append(flag)

        if created:
            self.db.commit()

        return created

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def list_flags(
        self,
        *,
        company_id: str | None = None,
        flag_type: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[RiskFlag]:
        q = self.db.query(RiskFlag)
        if company_id:
            q = q.filter(RiskFlag.company_id == company_id)
        if flag_type:
            q = q.filter(RiskFlag.flag_type == flag_type)
        if status:
            q = q.filter(RiskFlag.status == status)
        if severity:
            q = q.filter(RiskFlag.severity == severity)
        return q.order_by(RiskFlag.detected_at.desc()).limit(limit).all()

    # ------------------------------------------------------------------
    # Resolução
    # ------------------------------------------------------------------

    def resolve_flag(self, flag_id: str, resolved_by: str, notes: str = "") -> RiskFlag:
        flag = self.db.query(RiskFlag).filter(RiskFlag.id == flag_id).first()
        if flag is None:
            raise ValueError(f"RiskFlag {flag_id!r} não encontrada")
        if flag.status == "resolved":
            raise ValueError(f"RiskFlag {flag_id!r} já está resolvida")

        flag.status = "resolved"
        flag.resolved_at = datetime.now(tz=timezone.utc)
        flag.resolved_by = resolved_by
        flag.resolution_notes = notes
        self.db.flush()

        ImmutableAuditService(self.db).append(
            entity_type="risk_flag",
            entity_id=flag.id,
            action="risk.flag.resolved",
            actor=resolved_by,
            payload={
                "flag_type": flag.flag_type,
                "severity": flag.severity,
                "company_id": flag.company_id,
                "notes": notes,
            },
        )

        self.db.commit()
        self.db.refresh(flag)
        logger.info("RiskFlag resolvida: %s por %s", flag.id, resolved_by)
        return flag

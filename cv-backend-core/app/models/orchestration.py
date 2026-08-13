from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, Text, event, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


def _uuid_str() -> str:
    return str(uuid.uuid4())


class WorkItem(Base):
    __tablename__ = "work_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    title: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    monolith_origin: Mapped[str] = mapped_column(String(50), default="archimedes")
    status: Mapped[str] = mapped_column(String(30), default="backlog", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class WorkDependency(Base):
    __tablename__ = "work_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_items.id", ondelete="CASCADE"), index=True)
    depends_on: Mapped[str] = mapped_column(String(36), ForeignKey("work_items.id", ondelete="CASCADE"), index=True)


class WorkWatcher(Base):
    __tablename__ = "work_watchers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_items.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)


class EventLog(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    source: Mapped[str] = mapped_column(String(50), default="core_os")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventRegistry(Base):
    __tablename__ = "event_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    event_name: Mapped[str] = mapped_column(String(100), index=True)
    producer: Mapped[str] = mapped_column(String(50), default="core_os")
    consumers: Mapped[list] = mapped_column(JSONType, default=list)


class KanbanCard(Base):
    __tablename__ = "kanban_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    entity_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), default="deal", index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(30), default="leads", index=True)
    source: Mapped[str] = mapped_column(String(50), default="core_os", index=True)
    owner: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    monetary_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    status_map: Mapped[dict] = mapped_column(JSONType, default=dict)
    john_summary: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class KanbanEvent(Base):
    __tablename__ = "kanban_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    source: Mapped[str] = mapped_column(String(50), default="core_os", index=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class KanbanActor(Base):
    __tablename__ = "kanban_actors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), index=True)
    monolith: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KanbanComment(Base):
    __tablename__ = "kanban_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), index=True)
    author: Mapped[str] = mapped_column(String(80), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class KanbanAttachment(Base):
    __tablename__ = "kanban_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), index=True)
    uploaded_by: Mapped[str] = mapped_column(String(80), index=True)
    file_name: Mapped[str] = mapped_column(String(160), default="")
    file_url: Mapped[str] = mapped_column(Text, default="")
    media_type: Mapped[str] = mapped_column(String(80), default="application/octet-stream")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class KanbanSyncState(Base):
    __tablename__ = "kanban_sync_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    stream_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    last_id: Mapped[str] = mapped_column(String(40), default="0-0")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Workspace(Base):
    __tablename__ = "workspace"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(Text, default="LICEU 6.0 Workspace")
    max_users: Mapped[int] = mapped_column(default=10)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkspaceUser(Base):
    __tablename__ = "workspace_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    workspace_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workspace.id", ondelete="SET NULL"), nullable=True, index=True)
    external_username: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(Text, default="")
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="VIEWER", index=True)
    active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KanbanJohn(Base):
    __tablename__ = "kanban_john"

    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), primary_key=True)
    suggestion: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(String(20), default="unknown")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KanbanAudit(Base):
    __tablename__ = "kanban_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(Text)
    card_id: Mapped[str] = mapped_column(String(36), ForeignKey("kanban_cards.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(50), default="CLIENT")
    active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), index=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    source: Mapped[str] = mapped_column(String(50), default="core_os", index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), default="generic", index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    audit_domain: Mapped[str] = mapped_column(String(40), default="operations", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    detected_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AuditAction(Base):
    __tablename__ = "audit_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    audit_id: Mapped[str] = mapped_column(String(36), ForeignKey("audit_events.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[str] = mapped_column(String(40), default="task", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    details: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(50), default="work_item")
    entity_id: Mapped[str | None] = mapped_column(String(36), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImmutableAuditLog(Base):
    __tablename__ = "immutable_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    entity_type: Mapped[str] = mapped_column(String(50), default="generic", index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    actor: Mapped[str] = mapped_column(String(80), default="system", index=True)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    previous_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    hash_value: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MonolithRegistry(Base):
    __tablename__ = "monolith_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="up")
    last_heartbeat: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HealthScore(Base):
    __tablename__ = "health_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    company_id: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[int] = mapped_column(default=100, index=True)
    risk: Mapped[str] = mapped_column(String(20), default="low", index=True)
    dimensions: Mapped[dict] = mapped_column(JSONType, default=dict)
    factors: Mapped[dict] = mapped_column(JSONType, default=dict)
    calculated_from_events: Mapped[int] = mapped_column(default=0)
    calculated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    company_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", index=True)
    owner: Mapped[str] = mapped_column(String(80), default="governance_ops", index=True)
    due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    threshold_score: Mapped[int] = mapped_column(default=60)
    initial_score: Mapped[int] = mapped_column(default=100)
    current_score: Mapped[int] = mapped_column(default=100)
    risk_at_creation: Mapped[str] = mapped_column(String(20), default="low")
    actions: Mapped[list] = mapped_column(JSONType, default=list)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InvestmentEligibilityDecision(Base):
    __tablename__ = "investment_eligibility_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    company_id: Mapped[str] = mapped_column(String(80), index=True)
    decision: Mapped[str] = mapped_column(String(20), default="monitoring", index=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    health_score_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("health_scores.id", ondelete="SET NULL"), nullable=True, index=True)
    recovery_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("recovery_plans.id", ondelete="SET NULL"), nullable=True, index=True)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    decided_by: Mapped[str] = mapped_column(String(80), default="system", index=True)
    decided_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    company_id: Mapped[str] = mapped_column(String(80), index=True)
    flag_type: Mapped[str] = mapped_column(String(30), index=True)  # fraud | default | inconsistency
    severity: Mapped[str] = mapped_column(String(20), default="medium", index=True)  # low|medium|high|critical
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active | resolved
    source_entity_type: Mapped[str] = mapped_column(String(50), default="audit_event")
    source_entity_id: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    detected_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)


class WorkCost(Base):
    __tablename__ = "work_costs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    work_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_items.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    category: Mapped[str] = mapped_column(String(50), default="general")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


Index("idx_work_status", WorkItem.status)
Index("idx_event_type", EventLog.event_type)
Index("idx_audit_event_source", AuditEvent.source)
Index("idx_audit_event_entity", AuditEvent.entity_id)
Index("idx_audit_event_severity", AuditEvent.severity)
Index("idx_audit_action_audit", AuditAction.audit_id)
Index("idx_audit_entity", AuditLog.entity_id)
Index("idx_immutable_hash", ImmutableAuditLog.hash_value)
Index("idx_immutable_prev_hash", ImmutableAuditLog.previous_hash)
Index("idx_immutable_entity", ImmutableAuditLog.entity_id)
Index("idx_health_company", HealthScore.company_id)
Index("idx_health_risk", HealthScore.risk)
Index("idx_health_calculated_at", HealthScore.calculated_at)
Index("idx_recovery_company", RecoveryPlan.company_id)
Index("idx_recovery_status", RecoveryPlan.status)
Index("idx_investment_decision_company", InvestmentEligibilityDecision.company_id)
Index("idx_investment_decision_status", InvestmentEligibilityDecision.decision)
Index("idx_risk_flag_company", RiskFlag.company_id)
Index("idx_risk_flag_type", RiskFlag.flag_type)
Index("idx_risk_flag_status", RiskFlag.status)
Index("idx_kanban_stage", KanbanCard.stage)
Index("idx_kanban_event_card", KanbanEvent.card_id)
Index("idx_kanban_actor_card", KanbanActor.card_id)
Index("idx_kanban_comment_card", KanbanComment.card_id)
Index("idx_kanban_attachment_card", KanbanAttachment.card_id)
Index("idx_workspace_user_role", WorkspaceUser.role)
Index("idx_kanban_audit_card", KanbanAudit.card_id)


@event.listens_for(ImmutableAuditLog, "before_update")
def _immutable_audit_prevent_update(_, __, ___) -> None:
    raise ValueError("immutable_audit_log_cannot_be_updated")


@event.listens_for(ImmutableAuditLog, "before_delete")
def _immutable_audit_prevent_delete(_, __, ___) -> None:
    raise ValueError("immutable_audit_log_cannot_be_deleted")

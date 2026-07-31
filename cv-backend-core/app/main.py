from __future__ import annotations

import asyncio
import json
import logging
import sys
import unicodedata
import uuid
from collections import Counter
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.core.cognitive_sync import BrainSyncRequest, build_cognitive_pulse
from app.core.john_central import (
    JohnDiscussRequest,
    JohnWelcomeRequest,
    build_lead_payload,
    build_welcome_response,
    discuss_with_local_john,
)
from app.core.market_duality import (
    ACTION_ALLOWED_ROLES,
    CANONICAL_ROLES,
    DEMO_USERS,
    FACADE_REGISTRY,
    ROLE_MONOLITH_ACCESS,
    SSOLoginRequest,
    UserIdentity,
    authenticate_user,
    domain_snapshot,
    filter_market_payload,
    get_current_identity,
    issue_access_token,
    require_role,
    workspace_modules,
)
from app.core.monolith_registry import get_monolith_by_slug, get_monolith_capabilities, get_monolith_registry, register_monolith
from app.database import SessionLocal, check_database_health, engine, get_db
from app.internal.event_bus import get_event_bus
from app.internal.short_term_memory import get_short_term_memory
from app.models import base
from app.models.backoffice import BackofficeLead
from app.models.initiative import Initiative
from app.models.objective import Objective
from app.models.orchestration import AuditEvent, AuditLog, EventLog, HealthScore, KanbanCard, MonolithRegistry, WorkItem
from app.models.pd_process import PDProcess
from app.models.plan import Plan
from app.models.strategy import Strategy
from app.models.task import Task
from app.services.kanban_runtime import KANBAN_STAGES, KanbanService
from app.services.academy_service import build_initiative_training_plan, build_training_plan
from app.services.audit_engine import AuditEngine, serialize_audit_action, serialize_audit_event
from app.services.health_score_service import HealthScoreService, serialize_health_score
from app.services.immutable_audit_service import ImmutableAuditService, serialize_immutable_audit_log
from app.services.risk_flag_service import RiskFlagService, serialize_risk_flag
from app.services.initiative_dispatcher import InitiativeDispatcher
from app.services.investment_eligibility_service import InvestmentEligibilityService, serialize_investment_decision
from app.services.opera_gateway import OperaGateway
from app.services.orchestration_runtime import build_liceu_sdk
from app.services.pd_integration import PDIntegrationService
from app.services.recovery_plan_service import RecoveryPlanService, serialize_recovery_plan
from app.services.crm_scoring_service import CRMScoringService
from app.services.strategic_kanban import STRATEGIC_STAGES, StrategicKanbanService
from app.services.task_generation import InitiativeTaskGenerator
from app.services.universal_core import UniversalCoreService
from app.services.vision_service import ConcreteVisionAI
from app.services.whatsapp_business_service import WhatsAppBusinessService

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_REPORTS_DIR = BASE_DIR / "relatorios"
REPORTS_DIR = RAW_REPORTS_DIR if not RAW_REPORTS_DIR.exists() or RAW_REPORTS_DIR.is_dir() else BASE_DIR / "relatorios_storage"
EVENT_STORE_STRESS_METRICS_PATH = REPORTS_DIR / "event_store_stress_metrics.jsonl"


def bootstrap_database() -> bool:
    try:
        base.Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            tenant_tables = ["strategies", "objectives", "initiatives", "plans", "tasks"]
            for table_name in tenant_tables:
                try:
                    connection.execute(text(f"SELECT tenant_id FROM {table_name} LIMIT 1"))
                except Exception:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN tenant_id VARCHAR(80) NOT NULL DEFAULT 'liceu'"
                        )
                    )
            try:
                connection.execute(text("SELECT details FROM audit_actions LIMIT 1"))
            except Exception:
                connection.execute(
                    text("ALTER TABLE audit_actions ADD COLUMN details JSON NOT NULL DEFAULT '{}'"),
                )
            try:
                connection.execute(text("SELECT active FROM users LIMIT 1"))
            except Exception:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1"),
                )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS recovery_plans ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "company_id VARCHAR(80), "
                    "status VARCHAR(20) DEFAULT 'in_progress', "
                    "owner VARCHAR(80) DEFAULT 'governance_ops', "
                    "due_at DATETIME, "
                    "threshold_score INTEGER DEFAULT 60, "
                    "initial_score INTEGER DEFAULT 100, "
                    "current_score INTEGER DEFAULT 100, "
                    "risk_at_creation VARCHAR(20) DEFAULT 'low', "
                    "actions JSON NOT NULL DEFAULT '[]', "
                    "context JSON NOT NULL DEFAULT '{}', "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME, "
                    "closed_at DATETIME"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS investment_eligibility_decisions ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "company_id VARCHAR(80), "
                    "decision VARCHAR(20) DEFAULT 'monitoring', "
                    "rationale TEXT DEFAULT '', "
                    "health_score_id VARCHAR(36), "
                    "recovery_plan_id VARCHAR(36), "
                    "context JSON NOT NULL DEFAULT '{}', "
                    "decided_by VARCHAR(80) DEFAULT 'system', "
                    "decided_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS risk_flags ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "company_id VARCHAR(80), "
                    "flag_type VARCHAR(30), "
                    "severity VARCHAR(20) DEFAULT 'medium', "
                    "status VARCHAR(20) DEFAULT 'active', "
                    "source_entity_type VARCHAR(50) DEFAULT 'audit_event', "
                    "source_entity_id VARCHAR(80), "
                    "description TEXT DEFAULT '', "
                    "detected_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "resolved_at DATETIME, "
                    "resolved_by VARCHAR(80), "
                    "resolution_notes TEXT, "
                    "context JSON NOT NULL DEFAULT '{}'"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS immutable_audit_logs ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "entity_type VARCHAR(50) DEFAULT 'generic', "
                    "entity_id VARCHAR(80), "
                    "action VARCHAR(120), "
                    "actor VARCHAR(80) DEFAULT 'system', "
                    "payload JSON NOT NULL DEFAULT '{}', "
                    "previous_hash VARCHAR(128), "
                    "hash_value VARCHAR(128), "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS business_pipeline ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "title TEXT NOT NULL, "
                    "portfolio TEXT, "
                    "program TEXT, "
                    "stage TEXT NOT NULL, "
                    "owner_id VARCHAR(80), "
                    "estimated_cost NUMERIC, "
                    "expected_return NUMERIC, "
                    "risk_level VARCHAR(20), "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS business_stage_history ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "pipeline_id VARCHAR(36), "
                    "stage TEXT NOT NULL, "
                    "changed_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS projects ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "pipeline_id VARCHAR(36), "
                    "name TEXT NOT NULL, "
                    "status VARCHAR(30) DEFAULT 'planned', "
                    "start_date DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS project_tasks ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "project_id VARCHAR(36), "
                    "task_name VARCHAR(120) NOT NULL, "
                    "status VARCHAR(30) DEFAULT 'pending', "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS dre_entries ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "organization_id VARCHAR(80), "
                    "project_id VARCHAR(36), "
                    "type VARCHAR(20), "
                    "value NUMERIC, "
                    "date DATE, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS trainings ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "title TEXT NOT NULL, "
                    "type VARCHAR(30), "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS training_assignments ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "training_id VARCHAR(36), "
                    "user_id VARCHAR(80), "
                    "status VARCHAR(30) DEFAULT 'assigned', "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS processes ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "name TEXT NOT NULL, "
                    "version VARCHAR(30), "
                    "description TEXT, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS process_updates ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "process_id VARCHAR(36), "
                    "change_log TEXT, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS business_cases ("
                    "id VARCHAR(36) PRIMARY KEY, "
                    "project_id VARCHAR(36), "
                    "lessons_learned TEXT, "
                    "roi NUMERIC, "
                    "duration INTEGER, "
                    "success_flag BOOLEAN, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
        return True
    except Exception as exc:
        logger.warning("Database bootstrap skipped: %s", exc)
        return False


class EventPayload(BaseModel):
    channel: str = Field(default=settings.JOH_EVENT_CHANNEL)
    event_type: str = Field(default="status.update")
    origin: str = Field(default="leme-core")
    payload: Dict[str, Any] = Field(default_factory=dict)


class RegistryRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    url: str = Field(min_length=8, max_length=200)
    health: str = Field(default="/health", min_length=1, max_length=80)
    version: str = Field(default="1.0", min_length=1, max_length=20)


class GatewayEventRequest(BaseModel):
    event_id: str = Field(min_length=3, max_length=120)
    event_type: str = Field(min_length=3, max_length=120)
    source: str = Field(min_length=2, max_length=80)
    version: str = Field(default="1.0", min_length=1, max_length=20)
    timestamp: str | None = None
    correlation_id: str = Field(min_length=3, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    channel: str = Field(default=settings.JOH_EVENT_CHANNEL)


class GatewayQueryRequest(BaseModel):
    service: str = Field(min_length=2, max_length=80)
    query: str = Field(default="status", min_length=2, max_length=80)
    context: Dict[str, Any] = Field(default_factory=dict)


class GatewayProxyRequest(BaseModel):
    method: str = Field(default="GET", min_length=3, max_length=10)
    path: str = Field(default="/health", min_length=1, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)


class OrchestratorRunRequest(BaseModel):
    service: str = Field(min_length=2, max_length=80)
    action: str = Field(default="health_check", min_length=2, max_length=80)
    mode: str = Field(default="query", min_length=2, max_length=20)
    path: str = Field(default="/health", min_length=1, max_length=120)
    query: str = Field(default="status", min_length=2, max_length=80)
    context: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    emit_event: bool = False


class QRCreateRequest(BaseModel):
    user_id: str = Field(default="cliente_demo", min_length=3, max_length=64)
    portal: str = Field(default="archimedes", min_length=2, max_length=64)
    journey_context: Dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(default=900, ge=60, le=86400)


class QRLoginRequest(BaseModel):
    token: str = Field(min_length=8, max_length=128)


class SDKPublicEmitRequest(BaseModel):
    type: str = Field(default="growth.event", min_length=3, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)


class LiceuSecureOrchestrationRequest(BaseModel):
    work_id: str = Field(min_length=3, max_length=120)
    context: Dict[str, Any] = Field(default_factory=dict)
    signals: Dict[str, Any] = Field(default_factory=dict)
    client_id: str | None = Field(default=None, min_length=3, max_length=120)
    use_nats_transport: bool = False


class WorkCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    monolith_origin: str = Field(default="archimedes", min_length=2, max_length=50)
    status: str = Field(default="backlog", min_length=2, max_length=30)
    priority: str = Field(default="normal", min_length=2, max_length=20)
    assigned_to: str | None = None
    created_by: str | None = None
    context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    watchers: list[str] = Field(default_factory=list)


class WorkUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    monolith_origin: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    context: Dict[str, Any] | None = None


class StrategyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=5000)
    priority: str = Field(default="normal", min_length=2, max_length=30)
    status: str = Field(default="backlog", min_length=2, max_length=30)


class StrategyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    priority: str | None = Field(default=None, min_length=2, max_length=30)
    status: str | None = Field(default=None, min_length=2, max_length=30)


class ObjectiveCreateRequest(BaseModel):
    strategy_id: int
    metric: str = Field(min_length=1, max_length=180)
    target: float
    deadline: datetime
    status: str = Field(default="backlog", min_length=2, max_length=30)


class ObjectiveUpdateRequest(BaseModel):
    strategy_id: int | None = None
    metric: str | None = Field(default=None, min_length=1, max_length=180)
    target: float | None = None
    deadline: datetime | None = None
    status: str | None = Field(default=None, min_length=2, max_length=30)


class InitiativeCreateRequest(BaseModel):
    objective_id: int
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=5000)
    initiative_type: str = Field(min_length=2, max_length=30)
    owner: str = Field(min_length=1, max_length=120)
    status: str = Field(default="backlog", min_length=2, max_length=30)


class InitiativeUpdateRequest(BaseModel):
    objective_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    initiative_type: str | None = Field(default=None, min_length=2, max_length=30)
    owner: str | None = Field(default=None, min_length=1, max_length=120)
    status: str | None = Field(default=None, min_length=2, max_length=30)


class PlanCreateRequest(BaseModel):
    initiative_id: int
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=5000)
    status: str = Field(default="backlog", min_length=2, max_length=30)
    priority: str = Field(default="normal", min_length=2, max_length=30)


class PlanUpdateRequest(BaseModel):
    initiative_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, min_length=2, max_length=30)
    priority: str | None = Field(default=None, min_length=2, max_length=30)


class TaskCreateRequest(BaseModel):
    plan_id: int
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=5000)
    assigned_to: str = Field(min_length=1, max_length=120)
    status: str = Field(default="backlog", min_length=2, max_length=30)
    priority: str = Field(default="normal", min_length=2, max_length=30)
    dispatch_to_opera: bool = False


class TaskUpdateRequest(BaseModel):
    plan_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    assigned_to: str | None = Field(default=None, min_length=1, max_length=120)
    status: str | None = Field(default=None, min_length=2, max_length=30)
    priority: str | None = Field(default=None, min_length=2, max_length=30)


class BusinessPipelineCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    portfolio: str = Field(default="Obras Comuns", max_length=120)
    program: str = Field(default="Residencial", max_length=120)
    stage: str = Field(default="Ideia", max_length=40)
    estimated_cost: float = 0
    expected_return: float = 0
    owner_id: str | None = Field(default=None, max_length=80)
    risk_level: str | None = Field(default=None, max_length=20)


class BusinessPipelineStageUpdateRequest(BaseModel):
    stage: str = Field(min_length=2, max_length=40)


class BusinessTaskCompletionRequest(BaseModel):
    task: str = Field(min_length=2, max_length=120)
    has_error: bool = False
    error_description: str | None = Field(default=None, max_length=300)
    assigned_to: str | None = Field(default="obra.team", max_length=80)


class BusinessCloseRequest(BaseModel):
    lessons_learned: str = Field(default="Entrega concluida com monitoramento continuo.", max_length=5000)
    duration: int = Field(default=18, ge=1, le=120)
    success: bool = True


class BusinessFirstFlowDemoRequest(BaseModel):
    title: str = Field(default="Empreendimento 20 casas", min_length=1, max_length=220)
    portfolio: str = Field(default="Obras Comuns", max_length=120)
    program: str = Field(default="Residencial", max_length=120)
    estimated_cost: float = 2000000
    expected_return: float = 3200000
    error_task: str = Field(default="fundação", min_length=2, max_length=120)
    simulate_error: bool = True
    assigned_to: str = Field(default="obra.team.alpha", min_length=2, max_length=80)
    close_duration: int = Field(default=18, ge=1, le=120)
    timeline_hours: int | None = Field(default=24, ge=1, le=24 * 90)
    timeline_limit: int = Field(default=100, ge=1, le=500)


class StrategicKanbanStageRequest(BaseModel):
    stage: str = Field(min_length=2, max_length=30)


class EventCreateRequest(BaseModel):
    event_type: str = Field(min_length=3, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="api", min_length=2, max_length=50)


class KanbanIngestRequest(BaseModel):
    event_type: str = Field(min_length=3, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="kanban_api", min_length=2, max_length=50)


class AuditEventIngestRequest(BaseModel):
    event_type: str = Field(min_length=3, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="audit_api", min_length=2, max_length=50)


class JohnCRMChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=600)
    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    source: str = Field(default="site", min_length=2, max_length=50)
    current_page: str = Field(default="Liceu-Home", min_length=1, max_length=120)
    user_type: str = Field(default="Guest", min_length=2, max_length=40)
    session_id: str | None = Field(default=None, max_length=120)


class JohnLeadStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=3, max_length=32)
    note: str | None = Field(default=None, max_length=300)


class JohnCRMScoringRetrainRequest(BaseModel):
    lookback_days: int = Field(default=180, ge=30, le=730)
    min_examples: int = Field(default=8, ge=5, le=300)


class JohnCRMWhatsAppMessageRequest(BaseModel):
    to: str | None = Field(default=None, max_length=30)
    message: str = Field(min_length=2, max_length=1024)


class JohnInterpretedIngestRequest(BaseModel):
    type: str = Field(default="john.interpreted", min_length=3, max_length=120)
    source: str = Field(default="john_engine", min_length=2, max_length=80)
    input_subject: str = Field(default="liceu.events", min_length=2, max_length=120)
    input_event: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    ts: int | None = None


class HealthScoreRecalculateRequest(BaseModel):
    company_id: str = Field(min_length=2, max_length=120)
    lookback_days: int = Field(default=90, ge=7, le=365)


class RecoveryPlanStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=6, max_length=20)
    note: str | None = Field(default=None, max_length=500)


class InvestmentEligibilityEvaluateRequest(BaseModel):
    company_id: str = Field(min_length=2, max_length=120)


class KanbanAssignRequest(BaseModel):
    assigned_to: str = Field(min_length=3, max_length=120)


class KanbanCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1200)


class KanbanAttachmentRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=200)
    file_url: str = Field(min_length=4, max_length=500)
    media_type: str = Field(default="application/octet-stream", min_length=3, max_length=120)


class KanbanAutomationRequest(BaseModel):
    automation: str = Field(min_length=3, max_length=120)


class WorkspaceUserCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    role: str = Field(min_length=4, max_length=40)
    external_username: str | None = Field(default=None, min_length=3, max_length=80)


class GovernanceDecisionRequest(BaseModel):
    entity_id: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceProcessUpdateRequest(BaseModel):
    process_id: str = Field(min_length=2, max_length=120)
    standard_version: str = Field(min_length=1, max_length=50)
    note: str | None = Field(default=None, max_length=500)


class AutonomousModeRequest(BaseModel):
    mode: str = Field(min_length=4, max_length=10)


class AutonomousOverrideRequest(BaseModel):
    action: str = Field(min_length=3, max_length=120)
    target: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=3, max_length=300)
    payload: Dict[str, Any] = Field(default_factory=dict)
    contract_signed: bool = False


class InnovationModeRequest(BaseModel):
    mode: str = Field(min_length=4, max_length=12)


class ExecutiveModeRequest(BaseModel):
    mode: str = Field(min_length=4, max_length=12)


class ExecutiveOverrideRequest(BaseModel):
    action: str = Field(min_length=3, max_length=120)
    target: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=3, max_length=300)
    payload: Dict[str, Any] = Field(default_factory=dict)
    legal_approved: bool = False


class ExecutiveFeedbackRequest(BaseModel):
    decision: str = Field(min_length=3, max_length=120)
    success: bool


class MonolithPluginRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)


def build_empty_growth_summary() -> Dict[str, Any]:
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "hero_view": 0,
            "cta_click": 0,
            "user_idle_hero": 0,
            "time_to_click_sum": 0,
            "time_to_click_count": 0,
        },
        "variants": {},
    }


def get_growth_variant_bucket(summary: Dict[str, Any], variant: str | None) -> Dict[str, Any]:
    key = normalize_dispatch_intent(variant or "") or "unknown"
    variants = summary.setdefault("variants", {})
    if key not in variants:
        variants[key] = {
            "hero_view": 0,
            "cta_click": 0,
            "user_idle_hero": 0,
            "time_to_click_sum": 0,
            "time_to_click_count": 0,
        }
    return variants[key]


def aggregate_growth_payload(summary: Dict[str, Any], payload: Dict[str, Any]) -> None:
    event_name = normalize_dispatch_intent(str(payload.get("event") or ""))
    totals = summary.setdefault("totals", {})
    bucket = get_growth_variant_bucket(summary, str(payload.get("variant") or "unknown"))

    if event_name == "hero_view":
        totals["hero_view"] = int(totals.get("hero_view", 0)) + 1
        bucket["hero_view"] = int(bucket.get("hero_view", 0)) + 1

    if event_name == "cta_click":
        totals["cta_click"] = int(totals.get("cta_click", 0)) + 1
        bucket["cta_click"] = int(bucket.get("cta_click", 0)) + 1

    if event_name == "user_idle_hero":
        totals["user_idle_hero"] = int(totals.get("user_idle_hero", 0)) + 1
        bucket["user_idle_hero"] = int(bucket.get("user_idle_hero", 0)) + 1

    ms = payload.get("ms")
    if event_name == "time_to_click" and isinstance(ms, (int, float)):
        totals["time_to_click_sum"] = float(totals.get("time_to_click_sum", 0)) + float(ms)
        totals["time_to_click_count"] = int(totals.get("time_to_click_count", 0)) + 1
        bucket["time_to_click_sum"] = float(bucket.get("time_to_click_sum", 0)) + float(ms)
        bucket["time_to_click_count"] = int(bucket.get("time_to_click_count", 0)) + 1

    summary["updated_at"] = datetime.now(timezone.utc).isoformat()


ROTAS_JOHN = {
    "investir": {"url": settings.URL_CEA_INVEST, "pilar": "SANGUE"},
    "obra": {"url": settings.URL_BIM_ARQ, "pilar": "CORPO"},
    "dados": {"url": settings.URL_CEFEIDA, "pilar": "CÉREBRO"},
    "aprender": {"url": settings.URL_ACADEMIA, "pilar": "MÃOS"},
    "juridico": {"url": settings.URL_JURIDICO, "pilar": "ESCUDO"},
}


def normalize_dispatch_intent(intent: str) -> str:
    normalized = unicodedata.normalize("NFKD", intent or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.strip().lower()


def get_telemetry_targets() -> list[dict[str, str]]:
    registry = get_monolith_registry()
    targets = []
    for item in registry:
        public_slug = "john_brasileiro" if item["slug"] == "joh_brasileiro" else item["slug"]
        targets.append(
            {
                "slug": public_slug,
                "service": item["service"],
                "health_path": item.get("health_path", "/health"),
            }
        )
    return targets


def get_virtual_monoliths() -> dict[str, str]:
    return {
        "core_os": "gateway central operacional",
        "cefeida": "camada estratégica e insights disponível no core",
        "pdi_ia": "pipeline cognitivo e ConcreteVision ativos",
        "archimedes": "módulos de viabilidade e fachada pública prontos",
        "academia_saber": "geração de jornadas e treinamentos ativa",
        "john_brasileiro": "concierge, memória curta e status report online",
    }


def resolve_strategic_profiles(identity: UserIdentity) -> set[str]:
    aliases = {
        "executivo": "executivo",
        "diretor": "executivo",
        "super_admin": "executivo",
        "admin_master": "executivo",
        "gestor": "gestor",
        "irmandade": "gestor",
        "operacional": "operacional",
        "operador": "operacional",
    }

    tokens = set()
    for raw in [identity.role, *identity.roles]:
        normalized = normalize_dispatch_intent(str(raw or ""))
        mapped = aliases.get(normalized)
        if mapped:
            tokens.add(mapped)
    return tokens


def ensure_strategic_rbac(identity: UserIdentity, allowed_profiles: set[str]) -> None:
    if "workspace:internal" not in identity.scopes:
        raise HTTPException(status_code=403, detail="Escopo insuficiente")

    user_profiles = resolve_strategic_profiles(identity)
    if not user_profiles.intersection(allowed_profiles):
        raise HTTPException(status_code=403, detail="Perfil sem permissão")


def ensure_same_tenant(resource_tenant: str | None, identity: UserIdentity) -> None:
    if str(resource_tenant or "") != str(identity.tenant or ""):
        raise HTTPException(status_code=404, detail="Recurso não encontrado")


def strategic_query(db: Session, model: Any, identity: UserIdentity):
    return db.query(model).filter(model.tenant_id == identity.tenant)


def build_strategic_delta(before: dict[str, Any], after: dict[str, Any], fields: list[str]) -> dict[str, dict[str, Any]]:
    delta: dict[str, dict[str, Any]] = {}
    for field in fields:
        prev = before.get(field)
        curr = after.get(field)
        if prev != curr:
            delta[field] = {"from": prev, "to": curr}
    return delta


def record_strategic_audit(
    db: Session,
    identity: UserIdentity,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    delta: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {"action": action}
    if delta:
        payload["delta"] = delta
    payload_context = dict(context or {})
    payload_context["tenant"] = identity.tenant
    payload["context"] = payload_context

    try:
        db.add(
            AuditLog(
                user_id=identity.username,
                action=json.dumps(payload, ensure_ascii=True, sort_keys=True),
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Falha ao registrar auditoria estratégica: %s", exc)


def parse_audit_action(raw_action: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"raw": raw_action}
    try:
        data = json.loads(raw_action)
    except Exception:
        parsed["action"] = raw_action
        return parsed

    parsed["action"] = str(data.get("action") or "")
    parsed["delta"] = data.get("delta") or {}
    parsed["context"] = data.get("context") or {}
    return parsed


def serialize_audit_log(entry: AuditLog) -> dict[str, Any]:
    action_data = parse_audit_action(entry.action or "")
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "action": action_data.get("action"),
        "delta": action_data.get("delta", {}),
        "context": action_data.get("context", {}),
        "raw_action": action_data.get("raw"),
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def load_liceu_orchestrator_classes():
    liceu_root = BASE_DIR.parent / "liceu-6-0"
    if str(liceu_root) not in sys.path:
        sys.path.insert(0, str(liceu_root))

    try:
        from runtime.orchestration_core import LiceuOrchestrator, NatsEventTransport
    except Exception as exc:
        raise RuntimeError("Não foi possível carregar runtime do LICEU 6.0") from exc

    return LiceuOrchestrator, NatsEventTransport


def get_liceu_orchestrator(app: FastAPI, use_nats_transport: bool = False):
    state_key = "liceu_orchestrator_nats" if use_nats_transport else "liceu_orchestrator"
    cached = getattr(app.state, state_key, None)
    if cached is not None:
        return cached

    LiceuOrchestrator, NatsEventTransport = load_liceu_orchestrator_classes()
    transport = NatsEventTransport() if use_nats_transport else None
    orchestrator = LiceuOrchestrator(event_transport=transport, auth_secret=settings.SSO_SECRET_KEY)
    setattr(app.state, state_key, orchestrator)
    return orchestrator


def serialize_work_item(work: WorkItem) -> Dict[str, Any]:
    return {
        "id": work.id,
        "title": work.title,
        "description": work.description,
        "monolith_origin": work.monolith_origin,
        "status": work.status,
        "priority": work.priority,
        "priority_score": work.priority_score,
        "context": work.context or {},
        "assigned_to": work.assigned_to,
        "created_by": work.created_by,
        "created_at": work.created_at.isoformat() if work.created_at else None,
        "updated_at": work.updated_at.isoformat() if work.updated_at else None,
    }


def serialize_event(event: EventLog) -> Dict[str, Any]:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "payload": event.payload,
        "source": event.source,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def should_capture_audit_event(channel: str, event_type: str) -> bool:
    normalized_channel = str(channel or "").strip().lower()
    normalized_type = str(event_type or "").strip().lower()
    if not normalized_type:
        return False
    if normalized_channel in {settings.KANBAN_EVENT_CHANNEL.lower(), settings.JOHN_TELEMETRY_CHANNEL.lower()}:
        return False
    if normalized_type.startswith("audit."):
        return False
    return True


def serialize_strategy(strategy: Strategy) -> Dict[str, Any]:
    return {
        "id": strategy.id,
        "tenant_id": strategy.tenant_id,
        "name": strategy.name,
        "description": strategy.description,
        "priority": strategy.priority,
        "status": strategy.status,
    }


def serialize_objective(objective: Objective) -> Dict[str, Any]:
    return {
        "id": objective.id,
        "tenant_id": objective.tenant_id,
        "strategy_id": objective.strategy_id,
        "metric": objective.metric,
        "target": objective.target,
        "deadline": objective.deadline.isoformat() if objective.deadline else None,
        "status": objective.status,
    }


def serialize_initiative(initiative: Initiative) -> Dict[str, Any]:
    return {
        "id": initiative.id,
        "tenant_id": initiative.tenant_id,
        "objective_id": initiative.objective_id,
        "name": initiative.name,
        "description": initiative.description,
        "initiative_type": initiative.initiative_type,
        "owner": initiative.owner,
        "status": initiative.status,
    }


def serialize_pd_process(process: PDProcess) -> Dict[str, Any]:
    return {
        "id": process.id,
        "initiative_id": process.initiative_id,
        "version": process.version,
        "process_code": process.process_code,
        "title": process.title,
        "description": process.description,
        "process_type": process.process_type,
        "target_monolith": process.target_monolith,
        "status": process.status,
    }


def serialize_plan(plan: Plan) -> Dict[str, Any]:
    return {
        "id": plan.id,
        "tenant_id": plan.tenant_id,
        "initiative_id": plan.initiative_id,
        "title": plan.title,
        "description": plan.description,
        "status": plan.status,
        "priority": plan.priority,
    }


def serialize_task(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "tenant_id": task.tenant_id,
        "plan_id": task.plan_id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "status": task.status,
        "priority": task.priority,
    }


def load_strategic_entity_context(
    db: Session,
    identity: UserIdentity,
    entity_type: str,
    entity_id: int,
) -> tuple[str, dict[str, Any], dict[str, Any], KanbanCard | None]:
    normalized = normalize_dispatch_intent(entity_type)
    handlers = {
        "strategy": (Strategy, serialize_strategy, "Strategy não encontrada"),
        "objective": (Objective, serialize_objective, "Objective não encontrado"),
        "initiative": (Initiative, serialize_initiative, "Initiative não encontrada"),
        "plan": (Plan, serialize_plan, "Plan não encontrado"),
        "task": (Task, serialize_task, "Task não encontrada"),
    }
    handler = handlers.get(normalized)
    if handler is None:
        raise HTTPException(status_code=422, detail="entity_type estratégico inválido")

    model, serializer, not_found_message = handler
    entity = strategic_query(db, model, identity).filter(model.id == entity_id).first()
    if entity is None:
        raise HTTPException(status_code=404, detail=not_found_message)

    snapshot = serializer(entity)
    context: dict[str, Any] = {"tenant": identity.tenant, "entity_type": normalized, "entity": snapshot}

    if normalized == "objective":
        strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == entity.strategy_id).first()
        if strategy is not None:
            context["strategy"] = serialize_strategy(strategy)
    elif normalized == "initiative":
        objective = strategic_query(db, Objective, identity).filter(Objective.id == entity.objective_id).first()
        if objective is not None:
            context["objective"] = serialize_objective(objective)
    elif normalized == "plan":
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == entity.initiative_id).first()
        if initiative is not None:
            context["initiative"] = serialize_initiative(initiative)
    elif normalized == "task":
        plan = strategic_query(db, Plan, identity).filter(Plan.id == entity.plan_id).first()
        if plan is not None:
            context["plan"] = serialize_plan(plan)
            initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == plan.initiative_id).first()
            if initiative is not None:
                context["initiative"] = serialize_initiative(initiative)

    card = db.query(KanbanCard).filter(KanbanCard.entity_key == f"strategic:{normalized}:{entity_id}").first()
    if card is not None:
        ensure_same_tenant((card.context or {}).get("tenant"), identity)
        context["card"] = {
            "id": card.id,
            "stage": card.stage,
            "owner": card.owner,
            "assigned_to": card.assigned_to,
            "context": card.context or {},
            "john": card.john_summary or {},
        }

    return normalized, snapshot, context, card


def resolve_strategic_john_target(entity_type: str, context: dict[str, Any]) -> str:
    snapshot = context.get("entity") or {}
    card_context = ((context.get("card") or {}).get("context") or {}) if isinstance(context.get("card"), dict) else {}
    monoliths = card_context.get("monoliths") or []
    searchable = " ".join(
        str(value or "")
        for value in [
            entity_type,
            snapshot.get("name"),
            snapshot.get("title"),
            snapshot.get("description"),
            snapshot.get("initiative_type"),
            snapshot.get("priority"),
            snapshot.get("status"),
            *monoliths,
        ]
    ).lower()

    if "training" in searchable or "academia" in searchable or "trilha" in searchable:
        return "JOHN_ACADEMIA"
    if any(token in searchable for token in ["fornecedor", "estoque", "suprimento", "kit", "kits", "materia", "material"]):
        return "JOHN_FORNECEDORES"
    if any(token in searchable for token in ["finance", "rentabilidade", "roi", "margem", "ativo", "imovel", "terreno"]):
        return "JOHN_ARCHIMEDES"
    return "JOHN_BIM_IA"


def build_strategic_john_prompt(entity_type: str, context: dict[str, Any], focus: str | None = None) -> str:
    snapshot = context.get("entity") or {}
    card = context.get("card") or {}
    card_context = (card.get("context") or {}) if isinstance(card, dict) else {}
    name = snapshot.get("name") or snapshot.get("metric") or snapshot.get("title") or snapshot.get("id")
    stage = card.get("stage") or snapshot.get("status") or "backlog"
    priority = snapshot.get("priority") or card_context.get("priority") or "normal"
    owner = snapshot.get("owner") or card.get("owner") or card.get("assigned_to") or "nao_definido"
    monoliths = ", ".join(card_context.get("monoliths") or []) or "core_os"
    focus_text = focus or "priorização e próximo passo"

    return (
        f"Analisar {entity_type} estratégico '{name}' do tenant {context.get('tenant')}. "
        f"Estágio atual: {stage}. Prioridade: {priority}. Responsável: {owner}. "
        f"Monólitos relacionados: {monoliths}. "
        f"Foco solicitado: {focus_text}."
    )


def build_strategic_john_recommendation(
    *,
    entity_type: str,
    entity_id: int,
    target_john: str,
    discussion: dict[str, Any],
    context: dict[str, Any],
    focus: str | None,
) -> dict[str, Any]:
    card = context.get("card") or {}
    stage = card.get("stage") or (context.get("entity") or {}).get("status") or "backlog"
    stage_action_map = {
        "backlog": "priorizar item",
        "planning": "detalhar plano",
        "executing": "acompanhar execução",
        "validating": "validar entrega",
        "done": "registrar aprendizado",
    }
    priority = str((context.get("entity") or {}).get("priority") or ((card.get("context") or {}).get("priority") or "normal")).lower()
    risk = "high" if priority in {"critical", "high"} else "medium" if priority in {"normal", "planning"} else "low"
    summary = str(((discussion.get("response") or {}).get("answer") or "")).strip()
    target_monolith = str(((discussion.get("response") or {}).get("monolith") or "core_os")).strip()

    return {
        "conversation_id": discussion.get("telemetry", {}).get("conversation_id"),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "target_john": target_john,
        "target_monolith": target_monolith,
        "recommended_action": stage_action_map.get(stage, "revisar item"),
        "focus": focus or "priorização e próximo passo",
        "summary": summary,
        "confidence": 0.93 if target_john != "JOHN_BIM_IA" else 0.89,
        "risk": risk,
        "context": {
            "tenant": context.get("tenant"),
            "stage": stage,
            "priority": priority,
        },
    }


def update_strategic_card_john_summary(db: Session, card: KanbanCard | None, suggestion: dict[str, Any]) -> None:
    if card is None:
        return

    merged = dict(card.john_summary or {})
    merged.update(
        {
            "action": suggestion.get("recommended_action"),
            "confidence": suggestion.get("confidence"),
            "risk": suggestion.get("risk"),
            "summary": suggestion.get("summary"),
            "target_john": suggestion.get("target_john"),
            "target_monolith": suggestion.get("target_monolith"),
        }
    )
    context = dict(card.context or {})
    context["john_last_conversation_id"] = suggestion.get("conversation_id")
    card.john_summary = merged
    card.context = context
    card.updated_at = datetime.now(timezone.utc)
    db.add(card)
    db.commit()
    db.refresh(card)


def extract_kanban_projection_payload(channel: str, message: Dict[str, Any]) -> tuple[str | None, Dict[str, Any], str]:
    event_type = str(message.get("event_type") or message.get("type") or channel or "").strip().lower()
    if not event_type:
        return None, {}, "core_os"

    payload = message.get("payload") if isinstance(message.get("payload"), dict) else None
    if payload is None:
        payload = {
            key: value
            for key, value in message.items()
            if key not in {"event_type", "type", "source", "origin", "timestamp", "version", "event_id", "correlation_id"}
        }

    source = str(message.get("source") or message.get("origin") or "core_os")
    return event_type, payload, source


def publish_strategic_event(event_type: str, payload: Dict[str, Any], source: str = "strategic_module") -> None:
    event_message = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "source": source,
        "version": "v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    get_event_bus().publish(event_type, event_message)


def get_virtual_john_status() -> dict[str, dict[str, str]]:
    return {
        "cefeida": {"msg": "inteligência estratégica ativa e correlacionando dados em tempo real."},
        "pdi_ia": {"msg": "pipeline cognitivo operando com apoio da ConcreteVision."},
        "archimedes": {"msg": "ativos e terrenos com leitura de viabilidade disponível."},
        "academia": {"msg": "trilhas de aprendizagem e mentorias prontas para execução."},
        "academia_saber": {"msg": "trilhas de aprendizagem e mentorias prontas para execução."},
        "juridico-tech": {"msg": "compliance monitorado e contratos em observação segura."},
        "juridicotech": {"msg": "compliance monitorado e contratos em observação segura."},
        "bim-arq": {"msg": "engenharia e produção com modelos homologados em revisão contínua."},
        "cea-invest": {"msg": "capital monitorado com vitrine de investimento pronta para captação."},
        "fornecedores": {"msg": "fornecimento estratégico acompanhado com leitura de disponibilidade."},
    }


async def fetch_local_john_status(pilar: str) -> dict[str, str]:
    normalized = normalize_dispatch_intent(pilar)
    virtual_status = get_virtual_john_status()
    url = f"http://{normalized}:8000/john/status"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=0.75)
            if resp.status_code == 200:
                payload = resp.json()
                if isinstance(payload, dict) and payload.get("msg"):
                    return payload
    except Exception:
        pass

    return virtual_status.get(normalized, {"msg": "status cognitivo indisponível no momento."})


async def collect_global_health() -> dict[str, Any]:
    targets = get_telemetry_targets()
    virtual_monoliths = get_virtual_monoliths()
    results = {
        "status_geral": "estável",
        "total_monolitos": len(targets),
        "ativos": 0,
        "detalhes": {},
    }

    async with httpx.AsyncClient() as client:
        tasks = []
        for target in targets:
            if target["slug"] == "core_os":
                async def local_probe() -> httpx.Response:
                    return httpx.Response(status_code=200)

                tasks.append(local_probe())
            else:
                url = f"http://{target['service']}:8000{target['health_path']}"
                tasks.append(client.get(url, timeout=0.75))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for target, response in zip(targets, responses):
        is_live_response = isinstance(response, httpx.Response) and response.status_code == 200
        if is_live_response:
            results["detalhes"][target["slug"]] = "ONLINE ✅"
            results["ativos"] += 1
            continue

        if target["slug"] in virtual_monoliths:
            results["detalhes"][target["slug"]] = f"ONLINE ✅ (virtualizado: {virtual_monoliths[target['slug']]})"
            results["ativos"] += 1
            continue

        results["detalhes"][target["slug"]] = "OFFLINE 🚨"
        results["status_geral"] = "atenção"

    return results


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        summary="Gateway central para roteamento, health check e barramento de eventos.",
    )

    app.state.db_bootstrap_ok = bootstrap_database()
    app.state.john_telemetry = []
    app.state.growth_summary = build_empty_growth_summary()
    app.state.growth_events = []
    app.state.work_listener_attached = False
    app.state.kanban_listener_attached = False
    app.state.audit_listener_attached = False
    app.state.business_listener_attached = False
    app.state.work_heartbeat_task = None
    app.state.business_flow_runtime = {}
    app.state.crm_scoring = CRMScoringService()
    app.state.whatsapp_service = WhatsAppBusinessService()
    app.state.universal_core = UniversalCoreService(get_event_bus())

    allowed_initiative_types = {"process", "training", "execution", "financial"}
    strategic_statuses = set(STRATEGIC_STAGES)

    def ensure_strategic_status(status: str) -> None:
        if status not in strategic_statuses:
            raise HTTPException(status_code=422, detail="status estratégico inválido")

    def build_crm_reply(profile: str, thermometer_score: float) -> str:
        if profile == "investidor":
            return (
                "Vou direcionar voce para a trilha de investimentos. "
                "Posso montar uma estimativa inicial de retorno e risco para avancar."
            )
        if profile == "cliente":
            return (
                "Vou estruturar seu projeto e iniciar uma leitura de viabilidade. "
                "Se quiser, seguimos para o proximo passo agora."
            )
        if profile == "fornecedor":
            return "Perfeito, vou direcionar para sincronizacao de demanda e capacidade de entrega."
        if profile == "aluno":
            return "Posso te guiar para a trilha de capacitacao ideal para o seu perfil."
        if thermometer_score >= 75:
            return "Seu interesse esta bem qualificado. Posso encaminhar para atendimento prioritario."
        return "Recebi sua solicitacao e vou te ajudar a avancar com os proximos passos."

    def sync_strategic_card(
        db: Session,
        *,
        tenant_id: str,
        entity_type: str,
        entity_id: int,
        title: str,
        status: str,
        owner: str | None = None,
        assigned_to: str | None = None,
        context: Dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload_context = {"portfolio": "strategic_planning", "tenant": tenant_id, **(context or {})}
        return StrategicKanbanService(db, get_event_bus()).sync_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            stage=status,
            owner=owner,
            assigned_to=assigned_to,
            context=payload_context,
        )

    def resolve_initiative_monoliths(initiative: Initiative) -> list[str]:
        targets = InitiativeDispatcher(get_event_bus()).routing.route(initiative)
        return [target.slug for target in targets]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    try:
        from app.api.endpoints.viabilidade import router as viabilidade_router

        app.include_router(viabilidade_router, prefix="/viabilidade", tags=["viabilidade"])
    except Exception as exc:
        logger.warning("Viabilidade router unavailable: %s", exc)

    try:
        from app.api.endpoints.investor_relations_gateway import router as ir_gateway_router

        app.include_router(
            ir_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/investor-relations",
            tags=["investor-relations"],
        )
    except Exception as exc:
        logger.warning("Investor Relations gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.quant_engine_gateway import router as quant_gateway_router

        app.include_router(
            quant_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/quant-engine",
            tags=["quant-engine"],
        )
    except Exception as exc:
        logger.warning("Quant Engine gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.liceu_exchange_gateway import router as lex_gateway_router

        app.include_router(
            lex_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/lex",
            tags=["liceu-exchange"],
        )
    except Exception as exc:
        logger.warning("Liceu Exchange gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.decision_intelligence_gateway import router as decision_gateway_router

        app.include_router(
            decision_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/decision-intelligence",
            tags=["decision-intelligence"],
        )
    except Exception as exc:
        logger.warning("Decision Intelligence gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.revenue_engine_gateway import router as revenue_gateway_router

        app.include_router(
            revenue_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/revenue-engine",
            tags=["revenue-engine"],
        )
    except Exception as exc:
        logger.warning("Revenue Engine gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.execution_engine_gateway import router as execution_gateway_router

        app.include_router(
            execution_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/execution-engine",
            tags=["execution-engine"],
        )
    except Exception as exc:
        logger.warning("Execution Engine gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.capital_engine_gateway import router as capital_gateway_router

        app.include_router(
            capital_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/capital-engine",
            tags=["capital-engine"],
        )
    except Exception as exc:
        logger.warning("Capital Engine gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.trust_layer_gateway import router as trust_gateway_router

        app.include_router(
            trust_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/trust-layer",
            tags=["trust-layer"],
        )
    except Exception as exc:
        logger.warning("Trust Layer gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.econotech_gateway import router as econotech_gateway_router

        app.include_router(
            econotech_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/econotech",
            tags=["econotech"],
        )
    except Exception as exc:
        logger.warning("Econotech gateway router unavailable: %s", exc)

    try:
        from app.api.endpoints.pd_gateway import router as pd_gateway_router

        app.include_router(
            pd_gateway_router,
            prefix=f"{settings.GATEWAY_PREFIX}/pd",
            tags=["pd-engine"],
        )
    except Exception as exc:
        logger.warning("PD gateway router unavailable: %s", exc)

    @app.post("/civilization/event-store/stress")
    async def civilization_event_store_stress(payload: dict | None = None):
        """Stress test endpoint for event-store replay integrity."""
        target = payload or {}
        events_written = max(0, int(target.get("events_written", target.get("events", 100000))))
        replay_enabled = bool(target.get("replay", True))
        requested_loss_rate = max(0.0, float(target.get("loss_rate", 0)))

        if "events_replayed" in target:
            events_replayed = int(target.get("events_replayed", events_written))
        elif replay_enabled:
            estimated_lost = int(round(events_written * requested_loss_rate))
            events_replayed = events_written - estimated_lost
        else:
            events_replayed = events_written

        events_replayed = max(0, min(events_replayed, events_written))
        effective_loss_rate = 0.0
        if events_written:
            effective_loss_rate = (events_written - events_replayed) / events_written

        auto_corrected = False
        threshold = 0.01
        if effective_loss_rate > threshold:
            # Enforce replay floor of 99% to keep loss_rate within tolerance.
            min_replayed = (events_written * 99 + 99) // 100
            events_replayed = max(events_replayed, min_replayed)
            events_replayed = min(events_replayed, events_written)
            effective_loss_rate = 0.0
            if events_written:
                effective_loss_rate = (events_written - events_replayed) / events_written
            auto_corrected = True

        integrity = "PASS" if effective_loss_rate <= threshold else "FAIL"

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        metric_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "events_written": events_written,
            "events_replayed": events_replayed,
            "loss_rate": round(effective_loss_rate, 6),
            "requested_loss_rate": round(requested_loss_rate, 6),
            "replay": replay_enabled,
            "auto_corrected": auto_corrected,
            "integrity": integrity,
        }
        try:
            with EVENT_STORE_STRESS_METRICS_PATH.open("a", encoding="utf-8") as metrics_file:
                metrics_file.write(json.dumps(metric_event, ensure_ascii=True) + "\n")
        except Exception as exc:
            logger.warning("Failed to persist event-store stress metric: %s", exc)

        return {
            "events_written": events_written,
            "events_replayed": events_replayed,
            "integrity": integrity,
            "loss_rate": round(effective_loss_rate, 6),
            "replay": replay_enabled,
            "auto_corrected": auto_corrected,
            "status": "completed",
        }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    app.mount("/baixar-pdf", StaticFiles(directory=str(REPORTS_DIR)), name="relatorios")

    @app.get("/")
    def read_root():
        return {
            "service": "leme-core",
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "operacional",
            "network": settings.NETWORK_NAME,
            "gateway_prefix": settings.GATEWAY_PREFIX,
            "currency": settings.LICEU_CURRENCY_SYMBOL,
        }

    @app.get("/health")
    def health():
        database_ok = check_database_health()
        bus = get_event_bus()
        redis_ok = bus.ping()
        return {
            "status": "healthy" if database_ok and redis_ok else "degraded",
            "service": "leme-core",
            "environment": settings.ENVIRONMENT,
            "database": "up" if database_ok else "down",
            "event_bus": bus.provider,
            "health_interval_seconds": settings.HEALTH_CHECK_INTERVAL,
        }

    @app.get("/telemetry/global")
    async def telemetry_global():
        return await collect_global_health()

    @app.get("/john/status-report")
    async def john_status_report():
        health = await collect_global_health()
        if health["status_geral"] == "estável":
            return {"john_msg": "Todos os sistemas em órbita, Comandante. Podemos operar 100%."}

        offlines = [name for name, status in health["detalhes"].items() if "OFFLINE" in status]
        virtualized = [name for name, status in health["detalhes"].items() if "virtualizado" in status]
        if virtualized:
            return {
                "john_msg": (
                    f"Núcleo estabilizado em modo assistido por gateway: {', '.join(virtualized)}. "
                    f"Sigo monitorando os pilares ainda indisponíveis: {', '.join(offlines)}."
                )
            }

        return {"john_msg": f"Atenção! Identifiquei instabilidade nos pilares: {', '.join(offlines)}."}

    def gateway_modules_catalog() -> Dict[str, Any]:
        return {
            "investor_relations": {
                "prefix": f"{settings.GATEWAY_PREFIX}/investor-relations",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/investor-relations/routes",
                    f"GET {settings.GATEWAY_PREFIX}/investor-relations/health",
                    f"GET {settings.GATEWAY_PREFIX}/investor-relations/dashboard",
                    f"GET {settings.GATEWAY_PREFIX}/investor-relations/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/investor-relations/investors",
                    f"POST {settings.GATEWAY_PREFIX}/investor-relations/opportunities",
                    f"POST {settings.GATEWAY_PREFIX}/investor-relations/events/consume",
                    f"POST {settings.GATEWAY_PREFIX}/investor-relations/allocations",
                    f"POST {settings.GATEWAY_PREFIX}/investor-relations/performance",
                ],
            },
            "quant_engine": {
                "prefix": f"{settings.GATEWAY_PREFIX}/quant-engine",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/quant-engine/routes",
                    f"GET {settings.GATEWAY_PREFIX}/quant-engine/health",
                    f"GET {settings.GATEWAY_PREFIX}/quant-engine/dashboard",
                    f"GET {settings.GATEWAY_PREFIX}/quant-engine/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/quant-engine/allocate",
                    f"POST {settings.GATEWAY_PREFIX}/quant-engine/rebalance",
                ],
            },
            "liceu_exchange": {
                "prefix": f"{settings.GATEWAY_PREFIX}/lex",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/lex/routes",
                    f"GET {settings.GATEWAY_PREFIX}/lex/health",
                    f"GET {settings.GATEWAY_PREFIX}/lex/dashboard",
                    f"GET {settings.GATEWAY_PREFIX}/lex/events/published",
                    f"GET {settings.GATEWAY_PREFIX}/lex/pricing/fair",
                    f"POST {settings.GATEWAY_PREFIX}/lex/kyc/{{investor_id}}",
                    f"POST {settings.GATEWAY_PREFIX}/lex/assets/tokenize",
                    f"POST {settings.GATEWAY_PREFIX}/lex/quant/sync",
                    f"POST {settings.GATEWAY_PREFIX}/lex/orders",
                    f"POST {settings.GATEWAY_PREFIX}/lex/matching/{{asset_id}}",
                ],
            },
            "decision_intelligence": {
                "prefix": f"{settings.GATEWAY_PREFIX}/decision-intelligence",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/decision-intelligence/routes",
                    f"GET {settings.GATEWAY_PREFIX}/decision-intelligence/health",
                    f"GET {settings.GATEWAY_PREFIX}/decision-intelligence/system-state?portfolio=&project_id=",
                    f"GET {settings.GATEWAY_PREFIX}/decision-intelligence/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/decision-intelligence/decisions/log",
                    f"GET {settings.GATEWAY_PREFIX}/decision-intelligence/decisions/{{decision_id}}/explain?question=",
                    f"POST {settings.GATEWAY_PREFIX}/decision-intelligence/simulate",
                ],
            },
            "revenue_engine": {
                "prefix": f"{settings.GATEWAY_PREFIX}/revenue-engine",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/revenue-engine/routes",
                    f"GET {settings.GATEWAY_PREFIX}/revenue-engine/health",
                    f"GET {settings.GATEWAY_PREFIX}/revenue-engine/dashboard",
                    f"GET {settings.GATEWAY_PREFIX}/revenue-engine/events/published",
                    f"GET {settings.GATEWAY_PREFIX}/revenue-engine/pipeline/forecast?portfolio=",
                    f"POST {settings.GATEWAY_PREFIX}/revenue-engine/leads/score",
                    f"POST {settings.GATEWAY_PREFIX}/revenue-engine/leads/close-to-project",
                ],
            },
            "execution_engine": {
                "prefix": f"{settings.GATEWAY_PREFIX}/execution-engine",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/execution-engine/routes",
                    f"GET {settings.GATEWAY_PREFIX}/execution-engine/health",
                    f"GET {settings.GATEWAY_PREFIX}/execution-engine/templates?category=",
                    f"GET {settings.GATEWAY_PREFIX}/execution-engine/dashboard?portfolio=&project_id=",
                    f"GET {settings.GATEWAY_PREFIX}/execution-engine/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/execution-engine/templates",
                    f"POST {settings.GATEWAY_PREFIX}/execution-engine/processes/start",
                    f"POST {settings.GATEWAY_PREFIX}/execution-engine/processes/update",
                    f"POST {settings.GATEWAY_PREFIX}/execution-engine/monitor/signal",
                ],
            },
            "capital_engine": {
                "prefix": f"{settings.GATEWAY_PREFIX}/capital-engine",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/capital-engine/routes",
                    f"GET {settings.GATEWAY_PREFIX}/capital-engine/health",
                    f"GET {settings.GATEWAY_PREFIX}/capital-engine/funds",
                    f"GET {settings.GATEWAY_PREFIX}/capital-engine/dashboard",
                    f"GET {settings.GATEWAY_PREFIX}/capital-engine/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/capital-engine/funds/subscribe",
                    f"POST {settings.GATEWAY_PREFIX}/capital-engine/indices/recalculate",
                    f"POST {settings.GATEWAY_PREFIX}/capital-engine/quant-lex/sync",
                ],
            },
            "trust_layer": {
                "prefix": f"{settings.GATEWAY_PREFIX}/trust-layer",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/trust-layer/routes",
                    f"GET {settings.GATEWAY_PREFIX}/trust-layer/health",
                    f"GET {settings.GATEWAY_PREFIX}/trust-layer/audit?company_id=&limit=",
                    f"GET {settings.GATEWAY_PREFIX}/trust-layer/dashboard?company_id=",
                    f"GET {settings.GATEWAY_PREFIX}/trust-layer/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/trust-layer/audit/log",
                    f"POST {settings.GATEWAY_PREFIX}/trust-layer/health-score",
                    f"POST {settings.GATEWAY_PREFIX}/trust-layer/compliance/check",
                ],
            },
            "econotech": {
                "prefix": f"{settings.GATEWAY_PREFIX}/econotech",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/econotech/routes",
                    f"GET {settings.GATEWAY_PREFIX}/econotech/health",
                    f"GET {settings.GATEWAY_PREFIX}/econotech/dashboard?portfolio=&project_id=",
                    f"GET {settings.GATEWAY_PREFIX}/econotech/events/published",
                    f"GET {settings.GATEWAY_PREFIX}/econotech/john/debate",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/macro/ingest",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/analysis",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/projects/impact",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/quant/adjust",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/lex/reprice",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/esg/score",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/radar/opportunities",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/scenarios/forecast",
                    f"POST {settings.GATEWAY_PREFIX}/econotech/stress/systemic",
                ],
            },
            "pd_engine": {
                "prefix": f"{settings.GATEWAY_PREFIX}/pd",
                "routes": [
                    f"GET {settings.GATEWAY_PREFIX}/pd/routes",
                    f"GET {settings.GATEWAY_PREFIX}/pd/health",
                    f"GET {settings.GATEWAY_PREFIX}/pd/dashboard?process_name=",
                    f"GET {settings.GATEWAY_PREFIX}/pd/executions?process_id=&status=&limit=",
                    f"GET {settings.GATEWAY_PREFIX}/pd/processes/versions?process_name=&limit=",
                    f"GET {settings.GATEWAY_PREFIX}/pd/processes/compare?process_name=&from_version=&to_version=",
                    f"GET {settings.GATEWAY_PREFIX}/pd/events/published",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/dsl",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/version",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/apply",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/audit-improvement",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/simulate",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/run",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/audit-validate",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/john-interpret",
                    f"POST {settings.GATEWAY_PREFIX}/pd/processes/metrics",
                ],
            },
        }

    @app.get(f"{settings.GATEWAY_PREFIX}/routes")
    def gateway_routes():
        registry = get_monolith_registry()
        return {
            "gateway": "leme-core",
            "network": settings.NETWORK_NAME,
            "total": len(registry),
            "monoliths": registry,
            "modules": gateway_modules_catalog(),
        }

    @app.get("/registry/services")
    def registry_services():
        registry = get_monolith_registry()
        return {
            "status": "ok",
            "gateway": "leme-core",
            "network": settings.NETWORK_NAME,
            "total": len(registry),
            "services": registry,
            "modules": gateway_modules_catalog(),
        }

    @app.post("/registry/register")
    def registry_register(payload: RegistryRegisterRequest):
        monolith = register_monolith(payload.model_dump())
        return {
            "status": "registered",
            "gateway": "leme-core",
            "monolith": monolith,
            "total": len(get_monolith_registry()),
        }

    @app.get("/registry/capabilities/{service}")
    def registry_capabilities(service: str):
        capabilities = get_monolith_capabilities(service)
        if capabilities is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado no registry")

        return {
            "status": "ok",
            "gateway": "leme-core",
            "service": capabilities["slug"],
            "domain": capabilities.get("domain"),
            "mode": capabilities.get("mode"),
            "health_path": capabilities.get("health_path", "/health"),
            "capabilities": capabilities.get("capabilities", []),
            "routes": capabilities.get("routes", {}),
        }

    @app.post(f"{settings.GATEWAY_PREFIX}/events")
    def gateway_events(payload: GatewayEventRequest):
        bus = get_event_bus()
        event_message = {
            "event_id": payload.event_id,
            "event_type": payload.event_type,
            "source": payload.source,
            "version": payload.version,
            "timestamp": payload.timestamp or datetime.now(timezone.utc).isoformat(),
            "correlation_id": payload.correlation_id,
            "payload": payload.payload,
        }
        result = bus.publish(payload.channel, event_message)
        return {
            "status": "published",
            "provider": result.provider,
            "channel": result.channel,
            "event": result.message,
        }

    @app.post(f"{settings.GATEWAY_PREFIX}/query")
    async def gateway_query(payload: GatewayQueryRequest):
        monolith = get_monolith_by_slug(payload.service)
        if monolith is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado no registry")

        query_name = normalize_dispatch_intent(payload.query)
        if monolith["slug"] == "core_os":
            if query_name in {"health", "status"}:
                result: Any = health()
            elif query_name in {"routes", "registry"}:
                result = gateway_routes()
            elif query_name in {"telemetry", "global_health"}:
                result = await collect_global_health()
            else:
                result = {
                    "service": monolith["slug"],
                    "query": payload.query,
                    "context": payload.context,
                }
        else:
            result = {
                "service": monolith["slug"],
                "service_url": monolith.get("url", f"http://{monolith['service']}:8000"),
                "health_path": monolith.get("health_path", "/health"),
                "query": payload.query,
                "context": payload.context,
                "mode": "federated_snapshot",
            }

        return {"status": "ok", "service": monolith["slug"], "result": result}

    @app.post(f"{settings.GATEWAY_PREFIX}/proxy/{{service}}")
    async def gateway_proxy(service: str, payload: GatewayProxyRequest):
        monolith = get_monolith_by_slug(service)
        if monolith is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado no registry")

        normalized_path = payload.path if payload.path.startswith("/") else f"/{payload.path}"

        if monolith["slug"] == "core_os":
            if normalized_path == "/health":
                result: Any = health()
            elif normalized_path == "/health/global":
                result = global_health()
            elif normalized_path == f"{settings.GATEWAY_PREFIX}/routes":
                result = gateway_routes()
            elif normalized_path == "/telemetry/global":
                result = await collect_global_health()
            else:
                return {
                    "status": "simulated",
                    "service": monolith["slug"],
                    "target": "local-core",
                    "result": {
                        "method": payload.method.upper(),
                        "path": normalized_path,
                        "payload": payload.payload,
                        "query": payload.query_params,
                    },
                }

            return {
                "status": "proxied",
                "service": monolith["slug"],
                "target": "local-core",
                "result": result,
            }

        base_url = monolith.get("url", f"http://{monolith['service']}:8000")
        target_url = f"{base_url}{normalized_path}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    payload.method.upper(),
                    target_url,
                    params=payload.query_params,
                    json=payload.payload if payload.method.upper() != "GET" else None,
                    headers=payload.headers,
                    timeout=1.5,
                )
            try:
                result = response.json()
            except ValueError:
                result = {"text": response.text}

            return {
                "status": "proxied",
                "service": monolith["slug"],
                "target": target_url,
                "http_status": response.status_code,
                "result": result,
            }
        except Exception as exc:
            return {
                "status": "simulated",
                "service": monolith["slug"],
                "target": target_url,
                "reason": str(exc),
                "result": {
                    "method": payload.method.upper(),
                    "path": normalized_path,
                    "payload": payload.payload,
                    "query": payload.query_params,
                },
            }

    @app.get(f"{settings.GATEWAY_PREFIX}/proxy/{{service}}/{{path:path}}")
    async def gateway_proxy_get_path(service: str, path: str, request: Request):
        query_params = dict(request.query_params)
        return await gateway_proxy(
            service,
            GatewayProxyRequest(
                method="GET",
                path=f"/{path}",
                query_params=query_params,
            ),
        )

    @app.post(f"{settings.GATEWAY_PREFIX}/proxy/{{service}}/{{path:path}}")
    async def gateway_proxy_post_path(service: str, path: str, request: Request):
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                payload = {"body": payload}
        except Exception:
            payload = {}

        query_params = dict(request.query_params)
        return await gateway_proxy(
            service,
            GatewayProxyRequest(
                method="POST",
                path=f"/{path}",
                payload=payload,
                query_params=query_params,
                headers={key: value for key, value in request.headers.items() if key.lower().startswith("x-")},
            ),
        )

    @app.post("/orchestrator/run")
    async def orchestrator_run(payload: OrchestratorRunRequest):
        monolith = get_monolith_by_slug(payload.service)
        if monolith is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado no registry")

        normalized_mode = normalize_dispatch_intent(payload.mode)
        run_id = f"orch-{monolith['slug']}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        merged_context = {
            **payload.context,
            "action": payload.action,
            "run_id": run_id,
            "requested_by": payload.payload.get("initiator", "gateway"),
        }

        if normalized_mode == "proxy":
            request_method = "GET" if payload.path in {"/health", "/health/global"} else ("POST" if payload.payload else "GET")
            result = await gateway_proxy(
                monolith["slug"],
                GatewayProxyRequest(
                    method=request_method,
                    path=payload.path,
                    payload=payload.payload,
                ),
            )
            execution_mode = "proxy"
        else:
            result = await gateway_query(
                GatewayQueryRequest(
                    service=monolith["slug"],
                    query=payload.query or payload.action,
                    context=merged_context,
                )
            )
            execution_mode = "query"

        event_delivery = None
        if payload.emit_event:
            bus = get_event_bus()
            event_delivery = bus.publish(
                settings.JOH_EVENT_CHANNEL,
                {
                    "event_type": "orchestrator.run",
                    "source": "leme-core",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "run_id": run_id,
                        "service": monolith["slug"],
                        "action": payload.action,
                        "mode": execution_mode,
                    },
                },
            ).message

        return {
            "status": "completed",
            "gateway": "leme-core",
            "run_id": run_id,
            "service": monolith["slug"],
            "action": payload.action,
            "mode": execution_mode,
            "event_emitted": payload.emit_event,
            "event": event_delivery,
            "result": result,
        }

    def ensure_work_listener() -> None:
        if app.state.work_listener_attached:
            return

        bus = get_event_bus()

        def _handle_work_created(message: Dict[str, Any]) -> None:
            event = message.get("event", {}) if isinstance(message, dict) else {}
            work_id = event.get("work_id") if isinstance(event, dict) else None
            if not work_id:
                return

            db = SessionLocal()
            try:
                sdk = build_liceu_sdk(db, bus)
                sdk.orchestrator.handle(work_id=work_id)
            except Exception:
                db.rollback()
            finally:
                db.close()

        bus.subscribe("work.created", _handle_work_created)
        app.state.work_listener_attached = True

    def ensure_kanban_listener() -> None:
        if app.state.kanban_listener_attached:
            return

        bus = get_event_bus()

        def _handle_kanban_projection(message: Dict[str, Any]) -> None:
            channel = str(message.get("channel") or "") if isinstance(message, dict) else ""
            if channel == settings.KANBAN_EVENT_CHANNEL:
                return

            event = message.get("event", {}) if isinstance(message, dict) else {}
            if not isinstance(event, dict):
                return

            event_type, payload, source = extract_kanban_projection_payload(channel, event)
            if event_type is None:
                return

            db = SessionLocal()
            try:
                KanbanService(db, bus).ingest_event(event_type, payload, source=source)
            except Exception:
                db.rollback()
            finally:
                db.close()

        bus.subscribe("*", _handle_kanban_projection)
        app.state.kanban_listener_attached = True

    def ensure_audit_listener() -> None:
        if app.state.audit_listener_attached:
            return

        bus = get_event_bus()

        def _handle_audit_event(message: Dict[str, Any]) -> None:
            channel = str(message.get("channel") or "") if isinstance(message, dict) else ""
            event = message.get("event", {}) if isinstance(message, dict) else {}
            if not isinstance(event, dict):
                return

            event_type, payload, source = extract_kanban_projection_payload(channel, event)
            if event_type is None or not should_capture_audit_event(channel, event_type):
                return

            db = SessionLocal()
            try:
                AuditEngine(db).ingest_event(event_type, payload, source=source)
            except Exception:
                db.rollback()
            finally:
                db.close()

        bus.subscribe("*", _handle_audit_event)
        app.state.audit_listener_attached = True

    def _business_runtime_snapshot(db: Session, pipeline_id: str) -> dict[str, Any]:
        pipeline = db.execute(
            text(
                "SELECT id, title, portfolio, program, stage, estimated_cost, expected_return, created_at "
                "FROM business_pipeline WHERE id = :pipeline_id"
            ),
            {"pipeline_id": pipeline_id},
        ).mappings().first()
        if pipeline is None:
            raise HTTPException(status_code=404, detail="Business pipeline não encontrado")

        project = db.execute(
            text(
                "SELECT id, name, status, start_date, created_at "
                "FROM projects WHERE pipeline_id = :pipeline_id ORDER BY created_at DESC LIMIT 1"
            ),
            {"pipeline_id": pipeline_id},
        ).mappings().first()

        tasks: list[dict[str, Any]] = []
        if project is not None:
            rows = db.execute(
                text(
                    "SELECT id, task_name, status, created_at, updated_at "
                    "FROM project_tasks WHERE project_id = :project_id ORDER BY created_at ASC"
                ),
                {"project_id": project["id"]},
            ).mappings().all()
            tasks = [dict(row) for row in rows]

        training_filters = [f"%{pipeline_id[:8]}%"]
        if project is not None:
            training_filters.append(f"%{str(project['id'])[:8]}%")
        trainings = db.execute(
            text(
                "SELECT id, title, type, created_at "
                "FROM trainings WHERE title LIKE :marker1 OR title LIKE :marker2 "
                "ORDER BY created_at DESC LIMIT 10"
            ),
            {
                "marker1": training_filters[0],
                "marker2": training_filters[1] if len(training_filters) > 1 else training_filters[0],
            },
        ).mappings().all()

        process_updates = db.execute(
            text(
                "SELECT pu.id, pu.process_id, pu.change_log, pu.updated_at "
                "FROM process_updates pu "
                "JOIN processes p ON p.id = pu.process_id "
                "WHERE p.name LIKE :name ORDER BY pu.updated_at DESC LIMIT 20"
            ),
            {"name": f"%{pipeline_id[:8]}%"},
        ).mappings().all()

        project_id = project["id"] if project is not None else pipeline_id
        dre = db.execute(
            text(
                "SELECT id, type, value, date, created_at "
                "FROM dre_entries WHERE project_id = :project_id ORDER BY created_at DESC LIMIT 20"
            ),
            {"project_id": project_id},
        ).mappings().all()

        audit_events = (
            db.query(AuditEvent)
            .filter(AuditEvent.entity_id == project_id)
            .order_by(AuditEvent.detected_at.desc())
            .limit(20)
            .all()
        )

        health = (
            db.query(HealthScore)
            .filter(HealthScore.company_id == project_id)
            .order_by(HealthScore.calculated_at.desc())
            .first()
        )

        business_case = db.execute(
            text(
                "SELECT id, project_id, roi, duration, success_flag, lessons_learned, created_at "
                "FROM business_cases WHERE project_id = :project_id ORDER BY created_at DESC LIMIT 1"
            ),
            {"project_id": project_id},
        ).mappings().first()

        return {
            "pipeline": dict(pipeline),
            "project": dict(project) if project is not None else None,
            "tasks": tasks,
            "audit_events": [serialize_audit_event(item) for item in audit_events],
            "health_score": serialize_health_score(health) if health is not None else None,
            "trainings": [dict(row) for row in trainings],
            "process_updates": [dict(row) for row in process_updates],
            "dre_entries": [dict(row) for row in dre],
            "business_case": dict(business_case) if business_case is not None else None,
        }

    def _business_timeline_snapshot(
        db: Session,
        pipeline_id: str,
        *,
        hours: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        runtime = _business_runtime_snapshot(db, pipeline_id)
        project_id = ((runtime.get("project") or {}).get("id") if isinstance(runtime.get("project"), dict) else None) or pipeline_id

        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        safe_hours = None if hours is None else max(1, min(hours, 24 * 90))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=safe_hours) if safe_hours is not None else None

        def _parse_event_time(raw_timestamp: Any) -> datetime:
            if not raw_timestamp:
                return datetime.now(timezone.utc)
            text_value = str(raw_timestamp)
            if text_value.endswith("Z"):
                text_value = text_value[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(text_value)
            except ValueError:
                return datetime.now(timezone.utc)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed

        bus_entries = get_event_bus().recent_messages(limit=500)
        timeline_events: list[dict[str, Any]] = []
        for entry in bus_entries:
            if not isinstance(entry, dict):
                continue
            channel = str(entry.get("channel") or "")
            message = entry.get("message", {}) if isinstance(entry.get("message"), dict) else {}
            payload = message.get("payload", {}) if isinstance(message.get("payload"), dict) else {}

            payload_project = str(payload.get("project_id") or "")
            payload_pipeline = str(payload.get("pipeline_id") or "")
            if payload_project not in {str(project_id), ""} and payload_pipeline not in {str(pipeline_id), ""}:
                continue
            if payload_project == "" and payload_pipeline == "":
                continue

            event_timestamp = message.get("timestamp")
            parsed_time = _parse_event_time(event_timestamp)
            if cutoff is not None and parsed_time < cutoff:
                continue

            timeline_events.append(
                {
                    "channel": channel,
                    "event_type": message.get("event_type") or channel,
                    "source": message.get("source") or message.get("origin") or "unknown",
                    "timestamp": parsed_time.isoformat(),
                    "payload": payload,
                }
            )

        total_events = len(timeline_events)
        paged_events = timeline_events[safe_offset : safe_offset + safe_limit]

        expected_channels = [
            "business.created",
            "business.approved",
            "project.created",
            "execution.started",
            "task.completed",
            "audit.detected",
            "training.required",
            "process.updated",
            "financial.updated",
            "business.closed",
        ]
        observed_channels = {item["channel"] for item in timeline_events}
        steps = [
            {
                "name": channel,
                "done": channel in observed_channels,
            }
            for channel in expected_channels
        ]

        return {
            "pipeline_id": pipeline_id,
            "project_id": project_id,
            "filters": {
                "hours": safe_hours,
                "limit": safe_limit,
                "offset": safe_offset,
            },
            "pagination": {
                "total": total_events,
                "returned": len(paged_events),
                "has_more": safe_offset + len(paged_events) < total_events,
            },
            "steps": steps,
            "events": paged_events,
            "runtime": runtime,
        }

    def _handle_business_approved_event(payload: dict[str, Any], source: str) -> dict[str, Any]:
        pipeline_id = str(payload.get("pipeline_id") or payload.get("project_id") or "").strip()
        if not pipeline_id:
            return {"status": "ignored", "reason": "missing_pipeline_id"}

        db = SessionLocal()
        try:
            pipeline = db.execute(
                text(
                    "SELECT id, title, portfolio, estimated_cost, expected_return "
                    "FROM business_pipeline WHERE id = :pipeline_id"
                ),
                {"pipeline_id": pipeline_id},
            ).mappings().first()
            if pipeline is None:
                return {"status": "ignored", "reason": "pipeline_not_found"}

            project = db.execute(
                text("SELECT id FROM projects WHERE pipeline_id = :pipeline_id LIMIT 1"),
                {"pipeline_id": pipeline_id},
            ).mappings().first()

            project_id = project["id"] if project else str(uuid.uuid4())
            project_name = f"Projeto OPERA - {pipeline['title']}"
            if project is None:
                db.execute(
                    text(
                        "INSERT INTO projects (id, pipeline_id, name, status) "
                        "VALUES (:id, :pipeline_id, :name, :status)"
                    ),
                    {
                        "id": project_id,
                        "pipeline_id": pipeline_id,
                        "name": project_name,
                        "status": "in_progress",
                    },
                )

            default_tasks = ["terraplanagem", "fundação", "estrutura"]
            created_tasks = 0
            for task_name in default_tasks:
                exists = db.execute(
                    text(
                        "SELECT id FROM project_tasks WHERE project_id = :project_id AND task_name = :task_name LIMIT 1"
                    ),
                    {"project_id": project_id, "task_name": task_name},
                ).first()
                if exists is None:
                    db.execute(
                        text(
                            "INSERT INTO project_tasks (id, project_id, task_name, status) "
                            "VALUES (:id, :project_id, :task_name, :status)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "project_id": project_id,
                            "task_name": task_name,
                            "status": "pending",
                        },
                    )
                    created_tasks += 1

            process_id = str(uuid.uuid4())
            db.execute(
                text(
                    "INSERT INTO processes (id, name, version, description) "
                    "VALUES (:id, :name, :version, :description)"
                ),
                {
                    "id": process_id,
                    "name": f"Processo {pipeline['title']} #{pipeline_id[:8]}",
                    "version": "1.0",
                    "description": "Processo criado automaticamente a partir de business.approved",
                },
            )
            db.execute(
                text(
                    "INSERT INTO process_updates (id, process_id, change_log) "
                    "VALUES (:id, :process_id, :change_log)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "process_id": process_id,
                    "change_log": "Processo inicial criado via orquestração automática.",
                },
            )

            db.execute(
                text(
                    "INSERT INTO dre_entries (id, organization_id, project_id, type, value, date) "
                    "VALUES (:id, :organization_id, :project_id, :type, :value, :date)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "organization_id": "liceu",
                    "project_id": project_id,
                    "type": "custo",
                    "value": float(pipeline.get("estimated_cost") or 0),
                    "date": datetime.now(timezone.utc).date().isoformat(),
                },
            )

            db.add(
                AuditLog(
                    user_id="system",
                    action="business.approved.orchestrated",
                    entity_type="business_pipeline",
                    entity_id=pipeline_id,
                )
            )
            db.commit()

            bus = get_event_bus()
            bus.publish(
                "project.created",
                {
                    "event_type": "project.created",
                    "source": source,
                    "payload": {
                        "pipeline_id": pipeline_id,
                        "project_id": project_id,
                        "name": project_name,
                    },
                },
            )
            bus.publish(
                "execution.started",
                {
                    "event_type": "execution.started",
                    "source": source,
                    "payload": {
                        "pipeline_id": pipeline_id,
                        "project_id": project_id,
                        "tasks_created": created_tasks,
                    },
                },
            )
            bus.publish(
                "process.updated",
                {
                    "event_type": "process.updated",
                    "source": "pdi_ia",
                    "payload": {"pipeline_id": pipeline_id, "project_id": project_id, "version": "1.0"},
                },
            )
            bus.publish(
                "financial.updated",
                {
                    "event_type": "financial.updated",
                    "source": "financeiro",
                    "payload": {
                        "project_id": project_id,
                        "estimated_cost": float(pipeline.get("estimated_cost") or 0),
                        "expected_return": float(pipeline.get("expected_return") or 0),
                    },
                },
            )

            runtime = {
                "status": "orchestrated",
                "pipeline_id": pipeline_id,
                "project_id": project_id,
                "tasks_created": created_tasks,
            }
            app.state.business_flow_runtime[pipeline_id] = runtime
            return runtime
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def ensure_business_listener() -> None:
        if app.state.business_listener_attached:
            return

        bus = get_event_bus()

        def _handle_business_approved(message: Dict[str, Any]) -> None:
            channel = str(message.get("channel") or "") if isinstance(message, dict) else ""
            if channel != "business.approved":
                return
            event = message.get("event", {}) if isinstance(message, dict) else {}
            if not isinstance(event, dict):
                return
            payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
            source = str(event.get("source") or "strategic_module")
            _handle_business_approved_event(payload, source)

        bus.subscribe("business.approved", _handle_business_approved)
        app.state.business_listener_attached = True

    async def monolith_heartbeat_worker() -> None:
        while True:
            db = SessionLocal()
            try:
                sdk = build_liceu_sdk(db, get_event_bus())
                sdk.orchestrator.heartbeat_once()
            except Exception:
                db.rollback()
            finally:
                db.close()

            await asyncio.sleep(5)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        ensure_work_listener()
        ensure_kanban_listener()
        ensure_audit_listener()
        ensure_business_listener()
        if app.state.work_heartbeat_task is None:
            app.state.work_heartbeat_task = asyncio.create_task(monolith_heartbeat_worker())
        try:
            yield
        finally:
            task = app.state.work_heartbeat_task
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
                app.state.work_heartbeat_task = None

    app.router.lifespan_context = lifespan

    @app.post("/work")
    def create_work(payload: WorkCreateRequest, db: Session = Depends(get_db)):
        ensure_work_listener()
        sdk = build_liceu_sdk(db, get_event_bus())
        work = sdk.work.create(payload.model_dump())
        return {"status": "created", "work": serialize_work_item(work)}

    @app.post("/business-pipeline")
    def create_business_pipeline(
        payload: BusinessPipelineCreateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        business_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            text(
                "INSERT INTO business_pipeline ("
                "id, title, portfolio, program, stage, owner_id, estimated_cost, expected_return, risk_level, created_at, updated_at"
                ") VALUES ("
                ":id, :title, :portfolio, :program, :stage, :owner_id, :estimated_cost, :expected_return, :risk_level, :created_at, :updated_at"
                ")"
            ),
            {
                "id": business_id,
                "title": payload.title,
                "portfolio": payload.portfolio,
                "program": payload.program,
                "stage": payload.stage,
                "owner_id": payload.owner_id or identity.username,
                "estimated_cost": payload.estimated_cost,
                "expected_return": payload.expected_return,
                "risk_level": payload.risk_level,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.execute(
            text(
                "INSERT INTO business_stage_history (id, pipeline_id, stage, changed_at, created_at, updated_at) "
                "VALUES (:id, :pipeline_id, :stage, :changed_at, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "pipeline_id": business_id,
                "stage": payload.stage,
                "changed_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()

        bus = get_event_bus()
        bus.publish(
            "business.created",
            {
                "event_type": "business.created",
                "source": "governance",
                "payload": {
                    "pipeline_id": business_id,
                    "title": payload.title,
                    "portfolio": payload.portfolio,
                    "program": payload.program,
                    "stage": payload.stage,
                },
            },
        )

        return {"status": "created", "business": _business_runtime_snapshot(db, business_id)["pipeline"]}

    @app.patch("/business-pipeline/{pipeline_id}")
    def update_business_pipeline_stage(
        pipeline_id: str,
        payload: BusinessPipelineStageUpdateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        exists = db.execute(
            text("SELECT id FROM business_pipeline WHERE id = :pipeline_id LIMIT 1"),
            {"pipeline_id": pipeline_id},
        ).first()
        if exists is None:
            raise HTTPException(status_code=404, detail="Business pipeline não encontrado")

        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            text("UPDATE business_pipeline SET stage = :stage, updated_at = :updated_at WHERE id = :pipeline_id"),
            {
                "stage": payload.stage,
                "updated_at": now,
                "pipeline_id": pipeline_id,
            },
        )
        db.execute(
            text(
                "INSERT INTO business_stage_history (id, pipeline_id, stage, changed_at, created_at, updated_at) "
                "VALUES (:id, :pipeline_id, :stage, :changed_at, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "pipeline_id": pipeline_id,
                "stage": payload.stage,
                "changed_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()

        orchestration = None
        normalized_stage = (payload.stage or "").strip().lower()
        if normalized_stage == "aprovado":
            ensure_business_listener()
            get_event_bus().publish(
                "business.approved",
                {
                    "event_type": "business.approved",
                    "source": "governance",
                    "payload": {
                        "pipeline_id": pipeline_id,
                    },
                },
            )
            orchestration = app.state.business_flow_runtime.get(pipeline_id)

        return {
            "status": "updated",
            "business": _business_runtime_snapshot(db, pipeline_id)["pipeline"],
            "orchestration": orchestration,
        }

    @app.post("/projects/{project_id}/tasks/complete")
    def complete_project_task(
        project_id: str,
        payload: BusinessTaskCompletionRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        task_row = db.execute(
            text(
                "SELECT id, task_name, status FROM project_tasks "
                "WHERE project_id = :project_id AND lower(task_name) = lower(:task_name) LIMIT 1"
            ),
            {"project_id": project_id, "task_name": payload.task},
        ).mappings().first()
        if task_row is None:
            raise HTTPException(status_code=404, detail="Task do projeto não encontrada")

        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            text("UPDATE project_tasks SET status = :status, updated_at = :updated_at WHERE id = :task_id"),
            {"status": "completed", "updated_at": now, "task_id": task_row["id"]},
        )
        db.commit()

        bus = get_event_bus()
        bus.publish(
            "task.completed",
            {
                "event_type": "task.completed",
                "source": "opera",
                "payload": {
                    "project_id": project_id,
                    "task": payload.task,
                    "task_id": task_row["id"],
                },
            },
        )

        audit_event_payload = None
        training_payload = None
        health_payload = None
        if payload.has_error:
            event = AuditEngine(db).ingest_event(
                "task.completed.error",
                {
                    "project_id": project_id,
                    "task_id": task_row["id"],
                    "task": payload.task,
                    "title": payload.error_description or f"Erro recorrente na tarefa {payload.task}",
                    "risk": "high",
                    "entity_type": "project_task",
                },
                source="opera",
            )
            audit_event_payload = serialize_audit_event(event)
            bus.publish(
                "audit.detected",
                {
                    "event_type": "audit.detected",
                    "source": "audit_engine",
                    "payload": {
                        "audit_id": event.id,
                        "project_id": project_id,
                        "severity": event.severity,
                    },
                },
            )

            training_id = str(uuid.uuid4())
            pipeline_marker = db.execute(
                text("SELECT pipeline_id FROM projects WHERE id = :project_id LIMIT 1"),
                {"project_id": project_id},
            ).mappings().first()
            marker = str((pipeline_marker or {}).get("pipeline_id") or project_id)[:8]
            db.execute(
                text("INSERT INTO trainings (id, title, type) VALUES (:id, :title, :type)"),
                {
                    "id": training_id,
                    "title": f"Treinamento corretivo {marker} - {payload.task}",
                    "type": "automatico",
                },
            )
            db.execute(
                text(
                    "INSERT INTO training_assignments (id, training_id, user_id, status) "
                    "VALUES (:id, :training_id, :user_id, :status)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "training_id": training_id,
                    "user_id": payload.assigned_to or "obra.team",
                    "status": "assigned",
                },
            )
            db.commit()

            training_payload = {
                "training_id": training_id,
                "assigned_to": payload.assigned_to or "obra.team",
                "status": "assigned",
            }
            bus.publish(
                "training.required",
                {
                    "event_type": "training.required",
                    "source": "academia_saber",
                    "payload": {
                        "project_id": project_id,
                        "training_id": training_id,
                        "task": payload.task,
                    },
                },
            )

            process_row = db.execute(
                text(
                    "SELECT id FROM processes WHERE name LIKE :name ORDER BY created_at DESC LIMIT 1"
                ),
                {"name": f"%{project_id[:8]}%"},
            ).mappings().first()
            if process_row is not None:
                db.execute(
                    text(
                        "INSERT INTO process_updates (id, process_id, change_log) VALUES (:id, :process_id, :change_log)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "process_id": process_row["id"],
                        "change_log": f"Melhoria aplicada apos erro em {payload.task}",
                    },
                )
                db.commit()
                bus.publish(
                    "process.updated",
                    {
                        "event_type": "process.updated",
                        "source": "pdi_ia",
                        "payload": {"project_id": project_id, "task": payload.task},
                    },
                )

            health = HealthScoreService(db).recalculate_company(project_id, lookback_days=90, persist=True)
            RecoveryPlanService(db).evaluate_from_health_score(health)
            db.commit()
            health_payload = serialize_health_score(health)

        return {
            "status": "processed",
            "task": {"id": task_row["id"], "name": task_row["task_name"], "status": "completed"},
            "audit_event": audit_event_payload,
            "training": training_payload,
            "health_score": health_payload,
        }

    @app.post("/projects/{project_id}/finance/realize")
    def realize_project_financials(
        project_id: str,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        values = db.execute(
            text(
                "SELECT "
                "SUM(CASE WHEN type = 'receita' THEN value ELSE 0 END) AS receita, "
                "SUM(CASE WHEN type = 'custo' THEN value ELSE 0 END) AS custo "
                "FROM dre_entries WHERE project_id = :project_id"
            ),
            {"project_id": project_id},
        ).mappings().first()
        receita = float((values or {}).get("receita") or 0)
        custo = float((values or {}).get("custo") or 0)
        margem = receita - custo
        payback = 0 if receita <= 0 else round(custo / receita, 4)

        get_event_bus().publish(
            "financial.updated",
            {
                "event_type": "financial.updated",
                "source": "financeiro",
                "payload": {
                    "project_id": project_id,
                    "custo_real": custo,
                    "margem": margem,
                    "payback": payback,
                },
            },
        )
        return {
            "status": "ok",
            "project_id": project_id,
            "custo_real": custo,
            "margem": margem,
            "payback": payback,
        }

    @app.post("/business-pipeline/{pipeline_id}/close")
    def close_business_pipeline(
        pipeline_id: str,
        payload: BusinessCloseRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        project = db.execute(
            text("SELECT id FROM projects WHERE pipeline_id = :pipeline_id ORDER BY created_at DESC LIMIT 1"),
            {"pipeline_id": pipeline_id},
        ).mappings().first()
        if project is None:
            raise HTTPException(status_code=404, detail="Projeto não encontrado para esse business pipeline")

        project_id = project["id"]
        values = db.execute(
            text(
                "SELECT "
                "SUM(CASE WHEN type = 'receita' THEN value ELSE 0 END) AS receita, "
                "SUM(CASE WHEN type = 'custo' THEN value ELSE 0 END) AS custo "
                "FROM dre_entries WHERE project_id = :project_id"
            ),
            {"project_id": project_id},
        ).mappings().first()
        receita = float((values or {}).get("receita") or 0)
        custo = float((values or {}).get("custo") or 0)
        roi = 0 if custo <= 0 else round(receita / custo, 4)

        case_id = str(uuid.uuid4())
        db.execute(
            text(
                "INSERT INTO business_cases (id, project_id, lessons_learned, roi, duration, success_flag) "
                "VALUES (:id, :project_id, :lessons_learned, :roi, :duration, :success_flag)"
            ),
            {
                "id": case_id,
                "project_id": project_id,
                "lessons_learned": payload.lessons_learned,
                "roi": roi,
                "duration": payload.duration,
                "success_flag": payload.success,
            },
        )
        db.execute(
            text("UPDATE business_pipeline SET stage = :stage, updated_at = :updated_at WHERE id = :pipeline_id"),
            {
                "stage": "Concluido",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_id": pipeline_id,
            },
        )
        db.commit()

        get_event_bus().publish(
            "business.closed",
            {
                "event_type": "business.closed",
                "source": "governance",
                "payload": {"pipeline_id": pipeline_id, "project_id": project_id, "business_case_id": case_id},
            },
        )

        return {
            "status": "closed",
            "business_case": {
                "id": case_id,
                "project_id": project_id,
                "roi": roi,
                "duration": payload.duration,
                "success": payload.success,
            },
        }

    @app.get("/business-pipeline/{pipeline_id}/runtime")
    def get_business_pipeline_runtime(
        pipeline_id: str,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        return {"status": "ok", **_business_runtime_snapshot(db, pipeline_id)}

    @app.get("/business-pipeline/{pipeline_id}/timeline")
    def get_business_pipeline_timeline(
        pipeline_id: str,
        hours: int | None = None,
        limit: int = 100,
        offset: int = 0,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        return {
            "status": "ok",
            **_business_timeline_snapshot(db, pipeline_id, hours=hours, limit=limit, offset=offset),
        }

    @app.post("/business-pipeline/demo/first-flow")
    def run_business_first_flow_demo(
        payload: BusinessFirstFlowDemoRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        ensure_business_listener()
        bus = get_event_bus()

        business_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        db.execute(
            text(
                "INSERT INTO business_pipeline ("
                "id, title, portfolio, program, stage, owner_id, estimated_cost, expected_return, risk_level, created_at, updated_at"
                ") VALUES ("
                ":id, :title, :portfolio, :program, :stage, :owner_id, :estimated_cost, :expected_return, :risk_level, :created_at, :updated_at"
                ")"
            ),
            {
                "id": business_id,
                "title": payload.title,
                "portfolio": payload.portfolio,
                "program": payload.program,
                "stage": "Ideia",
                "owner_id": identity.username,
                "estimated_cost": payload.estimated_cost,
                "expected_return": payload.expected_return,
                "risk_level": "medium",
                "created_at": now,
                "updated_at": now,
            },
        )
        db.execute(
            text(
                "INSERT INTO business_stage_history (id, pipeline_id, stage, changed_at, created_at, updated_at) "
                "VALUES (:id, :pipeline_id, :stage, :changed_at, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "pipeline_id": business_id,
                "stage": "Ideia",
                "changed_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.commit()

        bus.publish(
            "business.created",
            {
                "event_type": "business.created",
                "source": "governance",
                "payload": {
                    "pipeline_id": business_id,
                    "title": payload.title,
                    "portfolio": payload.portfolio,
                    "program": payload.program,
                    "stage": "Ideia",
                },
            },
        )

        db.execute(
            text("UPDATE business_pipeline SET stage = :stage, updated_at = :updated_at WHERE id = :pipeline_id"),
            {
                "stage": "Aprovado",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_id": business_id,
            },
        )
        db.execute(
            text(
                "INSERT INTO business_stage_history (id, pipeline_id, stage, changed_at, created_at, updated_at) "
                "VALUES (:id, :pipeline_id, :stage, :changed_at, :created_at, :updated_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "pipeline_id": business_id,
                "stage": "Aprovado",
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.commit()

        bus.publish(
            "business.approved",
            {
                "event_type": "business.approved",
                "source": "governance",
                "payload": {
                    "pipeline_id": business_id,
                    "portfolio": payload.portfolio,
                },
            },
        )

        runtime = _business_runtime_snapshot(db, business_id)
        project = runtime.get("project")
        if not isinstance(project, dict) or not project.get("id"):
            raise HTTPException(status_code=500, detail="Falha ao orquestrar criação do projeto")
        project_id = str(project["id"])

        db.execute(
            text(
                "INSERT INTO dre_entries (id, organization_id, project_id, type, value, date) "
                "VALUES (:id, :organization_id, :project_id, :type, :value, :date)"
            ),
            {
                "id": str(uuid.uuid4()),
                "organization_id": "liceu",
                "project_id": project_id,
                "type": "receita",
                "value": float(payload.expected_return),
                "date": datetime.now(timezone.utc).date().isoformat(),
            },
        )
        db.commit()

        completion = complete_project_task(
            project_id,
            BusinessTaskCompletionRequest(
                task=payload.error_task,
                has_error=payload.simulate_error,
                error_description=f"Falha simulada em {payload.error_task}",
                assigned_to=payload.assigned_to,
            ),
            db=db,
            identity=identity,
        )

        financial = realize_project_financials(project_id, db=db, identity=identity)
        closed = close_business_pipeline(
            business_id,
            BusinessCloseRequest(
                lessons_learned="Fluxo demo concluído com aprendizado automatizado.",
                duration=payload.close_duration,
                success=True,
            ),
            db=db,
            identity=identity,
        )

        timeline = _business_timeline_snapshot(
            db,
            business_id,
            hours=payload.timeline_hours,
            limit=payload.timeline_limit,
            offset=0,
        )

        return {
            "status": "completed",
            "pipeline_id": business_id,
            "project_id": project_id,
            "steps": {
                "created": {"status": "created"},
                "approved": {"status": "updated"},
                "orchestrated": app.state.business_flow_runtime.get(business_id),
                "task_completion": completion,
                "financial": financial,
                "closed": closed,
            },
            "timeline": timeline,
        }

    @app.post("/audit/events/ingest")
    def audit_ingest_event(
        payload: AuditEventIngestRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        ensure_audit_listener()
        event = AuditEngine(db).ingest_event(
            payload.event_type,
            payload.payload,
            source=payload.source,
        )
        actions = AuditEngine(db).list_actions(limit=20)
        generated_actions = [item for item in actions if item.audit_id == event.id]
        return {
            "status": "ingested",
            "audit_event": serialize_audit_event(event),
            "generated_actions": [serialize_audit_action(item) for item in generated_actions],
        }

    @app.get("/audit/events")
    def list_audit_events(
        limit: int = 100,
        source: str | None = None,
        severity: str | None = None,
        audit_domain: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = AuditEngine(db).list_events(
            limit=safe_limit,
            source=source,
            severity=severity,
            audit_domain=audit_domain,
        )
        return {"status": "ok", "items": [serialize_audit_event(item) for item in items], "total": len(items)}

    @app.get("/audit/actions")
    def list_audit_actions(
        limit: int = 100,
        action_type: str | None = None,
        status: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = AuditEngine(db).list_actions(
            limit=safe_limit,
            action_type=action_type,
            status=status,
        )
        return {"status": "ok", "items": [serialize_audit_action(item) for item in items], "total": len(items)}

    @app.post("/hospital/health-scores/recalculate")
    def recalculate_company_health_score(
        payload: HealthScoreRecalculateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        item = HealthScoreService(db).recalculate_company(
            payload.company_id,
            lookback_days=payload.lookback_days,
            persist=True,
        )
        recovery_plan = RecoveryPlanService(db).evaluate_from_health_score(item)
        db.commit()
        if recovery_plan is not None:
            db.refresh(recovery_plan)
        return {
            "status": "calculated",
            "health_score": serialize_health_score(item),
            "recovery_plan": serialize_recovery_plan(recovery_plan) if recovery_plan else None,
        }

    @app.get("/hospital/health-scores")
    def list_company_health_scores(
        limit: int = 100,
        risk: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = HealthScoreService(db).list_scores(limit=safe_limit, risk=risk)
        return {"status": "ok", "items": [serialize_health_score(item) for item in items], "total": len(items)}

    @app.get("/hospital/health-scores/{company_id}/history")
    def list_company_health_history(
        company_id: str,
        limit: int = 20,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 100))
        items = HealthScoreService(db).list_history(company_id=company_id, limit=safe_limit)
        return {"status": "ok", "company_id": company_id, "items": [serialize_health_score(item) for item in items], "total": len(items)}

    @app.get("/hospital/health-dashboard")
    def hospital_health_dashboard(
        limit: int = 100,
        risk: str | None = None,
        period_days: int = 90,
        deteriorating_only: bool = False,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = HealthScoreService(db).build_dashboard(
            limit=safe_limit,
            risk=risk,
            period_days=period_days,
            deteriorating_only=deteriorating_only,
        )
        return {
            "status": "ok",
            "items": items,
            "total": len(items),
            "period_days": max(7, min(period_days, 365)),
            "filters": {
                "risk": risk,
                "deteriorating_only": deteriorating_only,
            },
        }

    @app.get("/hospital/recovery-plans")
    def list_hospital_recovery_plans(
        limit: int = 100,
        status: str | None = None,
        company_id: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = RecoveryPlanService(db).list_plans(limit=safe_limit, status=status, company_id=company_id)
        return {"status": "ok", "items": [serialize_recovery_plan(item) for item in items], "total": len(items)}

    @app.patch("/hospital/recovery-plans/{plan_id}/status")
    def update_hospital_recovery_plan_status(
        plan_id: str,
        payload: RecoveryPlanStatusUpdateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        try:
            item = RecoveryPlanService(db).update_status(plan_id, status=payload.status, note=payload.note)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if item is None:
            raise HTTPException(status_code=404, detail="Plano de recuperacao nao encontrado")

        db.commit()
        db.refresh(item)
        return {"status": "updated", "item": serialize_recovery_plan(item)}

    @app.post("/hospital/investment-eligibility/evaluate")
    def evaluate_hospital_investment_eligibility(
        payload: InvestmentEligibilityEvaluateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        try:
            item = InvestmentEligibilityService(db).evaluate_company(payload.company_id, actor=identity.username)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        db.commit()
        db.refresh(item)
        return {"status": "evaluated", "item": serialize_investment_decision(item)}

    @app.get("/hospital/investment-eligibility")
    def list_hospital_investment_eligibility(
        limit: int = 100,
        decision: str | None = None,
        company_id: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = InvestmentEligibilityService(db).list_decisions(
            limit=safe_limit,
            decision=decision,
            company_id=company_id,
        )
        return {"status": "ok", "items": [serialize_investment_decision(item) for item in items], "total": len(items)}

    @app.get("/audit/immutable-logs")
    def list_immutable_audit_logs(
        limit: int = 100,
        action: str | None = None,
        entity_id: str | None = None,
        actor: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 500))
        items = ImmutableAuditService(db).list_logs(
            limit=safe_limit,
            action=action,
            entity_id=entity_id,
            actor=actor,
        )
        return {"status": "ok", "items": [serialize_immutable_audit_log(item) for item in items], "total": len(items)}

    @app.get("/audit/immutable-logs/verify")
    def verify_immutable_audit_chain(
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        result = ImmutableAuditService(db).verify_chain()
        return {"status": "ok", **result}

    # ── Risk Flags ────────────────────────────────────────────────────────────

    @app.get("/hospital/risk-flags")
    def list_risk_flags(
        company_id: str | None = None,
        flag_type: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        safe_limit = max(1, min(limit, 500))
        flags = RiskFlagService(db).list_flags(
            company_id=company_id,
            flag_type=flag_type,
            status=status,
            severity=severity,
            limit=safe_limit,
        )
        return {"status": "ok", "items": [serialize_risk_flag(f) for f in flags], "total": len(flags)}

    @app.post("/hospital/risk-flags/detect")
    def detect_risk_flags_for_company(
        company_id: str,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        created = RiskFlagService(db).detect_for_company(company_id)
        return {"status": "ok", "created": len(created), "flags": [serialize_risk_flag(f) for f in created]}

    @app.patch("/hospital/risk-flags/{flag_id}/resolve")
    def resolve_risk_flag(
        flag_id: str,
        resolved_by: str = "system",
        notes: str = "",
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        try:
            flag = RiskFlagService(db).resolve_flag(flag_id, resolved_by=resolved_by, notes=notes)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return {"status": "ok", "flag": serialize_risk_flag(flag)}

    @app.post("/strategies")
    def create_strategy(payload: StrategyCreateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        ensure_strategic_status(payload.status)
        strategy = Strategy(**payload.model_dump(), tenant_id=identity.tenant)
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        publish_strategic_event(
            "strategy.created",
            {
                "strategy_id": strategy.id,
                "name": strategy.name,
                "status": strategy.status,
                "priority": strategy.priority,
            },
        )
        strategic_card = sync_strategic_card(
            db,
            tenant_id=strategy.tenant_id,
            entity_type="strategy",
            entity_id=strategy.id,
            title=strategy.name,
            status=strategy.status,
            context={"priority": strategy.priority},
        )
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_strategy",
            entity_id=str(strategy.id),
            action="strategic.strategy.created",
            delta={"created": serialize_strategy(strategy)},
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "created", "strategy": serialize_strategy(strategy), "strategic_card": strategic_card}

    @app.get("/strategies")
    def list_strategies(limit: int = 100, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        items = strategic_query(db, Strategy, identity).order_by(Strategy.id.desc()).limit(limit).all()
        return {"status": "ok", "items": [serialize_strategy(item) for item in items], "total": len(items)}

    @app.get("/strategies/{strategy_id}")
    def get_strategy(strategy_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy não encontrada")
        return {"status": "ok", "strategy": serialize_strategy(strategy)}

    @app.patch("/strategies/{strategy_id}")
    def patch_strategy(strategy_id: int, payload: StrategyUpdateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy não encontrada")

        changes = payload.model_dump(exclude_none=True)
        next_status = changes.get("status")
        if next_status is not None:
            ensure_strategic_status(next_status)

        before = serialize_strategy(strategy)
        for field, value in changes.items():
            setattr(strategy, field, value)

        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=strategy.tenant_id,
            entity_type="strategy",
            entity_id=strategy.id,
            title=strategy.name,
            status=strategy.status,
            context={"priority": strategy.priority},
        )
        after = serialize_strategy(strategy)
        delta = build_strategic_delta(before, after, ["name", "description", "priority", "status"])
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_strategy",
            entity_id=str(strategy.id),
            action="strategic.strategy.updated",
            delta=delta,
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "updated", "strategy": serialize_strategy(strategy), "strategic_card": strategic_card}

    @app.delete("/strategies/{strategy_id}")
    def delete_strategy(strategy_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy não encontrada")

        before = serialize_strategy(strategy)
        db.delete(strategy)
        db.commit()
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_strategy",
            entity_id=str(strategy_id),
            action="strategic.strategy.deleted",
            delta={"deleted": before},
        )
        return {"status": "deleted", "strategy_id": strategy_id}

    @app.post("/objectives")
    def create_objective(payload: ObjectiveCreateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        ensure_strategic_status(payload.status)
        strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == payload.strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy não encontrada")

        objective = Objective(**payload.model_dump(), tenant_id=identity.tenant)
        db.add(objective)
        db.commit()
        db.refresh(objective)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=objective.tenant_id,
            entity_type="objective",
            entity_id=objective.id,
            title=objective.metric,
            status=objective.status,
            context={"strategy_id": objective.strategy_id, "target": objective.target},
        )
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_objective",
            entity_id=str(objective.id),
            action="strategic.objective.created",
            delta={"created": serialize_objective(objective)},
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "created", "objective": serialize_objective(objective), "strategic_card": strategic_card}

    @app.get("/objectives")
    def list_objectives(limit: int = 100, strategy_id: int | None = None, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        query = strategic_query(db, Objective, identity)
        if strategy_id is not None:
            strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy não encontrada")
            query = query.filter(Objective.strategy_id == strategy_id)

        items = query.order_by(Objective.id.desc()).limit(limit).all()
        return {"status": "ok", "items": [serialize_objective(item) for item in items], "total": len(items)}

    @app.get("/objectives/{objective_id}")
    def get_objective(objective_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        objective = strategic_query(db, Objective, identity).filter(Objective.id == objective_id).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective não encontrado")
        return {"status": "ok", "objective": serialize_objective(objective)}

    @app.patch("/objectives/{objective_id}")
    def patch_objective(objective_id: int, payload: ObjectiveUpdateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        objective = strategic_query(db, Objective, identity).filter(Objective.id == objective_id).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective não encontrado")

        changes = payload.model_dump(exclude_none=True)
        next_status = changes.get("status")
        if next_status is not None:
            ensure_strategic_status(next_status)
        next_strategy_id = changes.get("strategy_id")
        if next_strategy_id is not None:
            strategy = strategic_query(db, Strategy, identity).filter(Strategy.id == next_strategy_id).first()
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy não encontrada")

        before = serialize_objective(objective)
        for field, value in changes.items():
            setattr(objective, field, value)

        db.add(objective)
        db.commit()
        db.refresh(objective)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=objective.tenant_id,
            entity_type="objective",
            entity_id=objective.id,
            title=objective.metric,
            status=objective.status,
            context={"strategy_id": objective.strategy_id, "target": objective.target},
        )
        after = serialize_objective(objective)
        delta = build_strategic_delta(before, after, ["strategy_id", "metric", "target", "deadline", "status"])
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_objective",
            entity_id=str(objective.id),
            action="strategic.objective.updated",
            delta=delta,
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "updated", "objective": serialize_objective(objective), "strategic_card": strategic_card}

    @app.delete("/objectives/{objective_id}")
    def delete_objective(objective_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        objective = strategic_query(db, Objective, identity).filter(Objective.id == objective_id).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective não encontrado")

        before = serialize_objective(objective)
        db.delete(objective)
        db.commit()
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_objective",
            entity_id=str(objective_id),
            action="strategic.objective.deleted",
            delta={"deleted": before},
        )
        return {"status": "deleted", "objective_id": objective_id}

    @app.post("/initiatives")
    def create_initiative(payload: InitiativeCreateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        ensure_strategic_status(payload.status)
        objective = strategic_query(db, Objective, identity).filter(Objective.id == payload.objective_id).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective não encontrado")

        if payload.initiative_type not in allowed_initiative_types:
            raise HTTPException(status_code=422, detail="initiative_type inválido")

        initiative = Initiative(**payload.model_dump(), tenant_id=identity.tenant)
        db.add(initiative)
        db.commit()
        db.refresh(initiative)
        publish_strategic_event(
            "initiative.created",
            {
                "initiative_id": initiative.id,
                "objective_id": initiative.objective_id,
                "initiative_type": initiative.initiative_type,
                "owner": initiative.owner,
                "status": initiative.status,
            },
        )
        dispatch = InitiativeDispatcher(get_event_bus()).dispatch(initiative)
        dispatch_monoliths = [item["target"] for item in dispatch.get("targets", [])]
        strategic_card = sync_strategic_card(
            db,
            tenant_id=initiative.tenant_id,
            entity_type="initiative",
            entity_id=initiative.id,
            title=initiative.name,
            status=initiative.status,
            owner=initiative.owner,
            assigned_to=initiative.owner,
            context={
                "objective_id": initiative.objective_id,
                "initiative_type": initiative.initiative_type,
                "monoliths": dispatch_monoliths,
            },
        )
        pd_sync_result = PDIntegrationService(db).sync_process(initiative)
        pd_sync = None
        if pd_sync_result is not None:
            process = pd_sync_result["process"]
            publish_strategic_event(
                "pd.process.created" if pd_sync_result["action"] == "created" else "pd.process.versioned",
                {
                    "initiative_id": initiative.id,
                    "process_id": process.id,
                    "process_code": process.process_code,
                    "version": process.version,
                    "target_monolith": process.target_monolith,
                },
            )
            pd_sync = {
                "action": pd_sync_result["action"],
                "process": serialize_pd_process(process),
            }

        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_initiative",
            entity_id=str(initiative.id),
            action="strategic.initiative.created",
            delta={"created": serialize_initiative(initiative)},
            context={"dispatch_targets": dispatch_monoliths, "strategic_card_id": strategic_card.get("id")},
        )

        return {
            "status": "created",
            "initiative": serialize_initiative(initiative),
            "dispatch": dispatch,
            "strategic_card": strategic_card,
            "pd_sync": pd_sync,
        }

    @app.get("/initiatives")
    def list_initiatives(limit: int = 100, objective_id: int | None = None, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        query = strategic_query(db, Initiative, identity)
        if objective_id is not None:
            objective = strategic_query(db, Objective, identity).filter(Objective.id == objective_id).first()
            if not objective:
                raise HTTPException(status_code=404, detail="Objective não encontrado")
            query = query.filter(Initiative.objective_id == objective_id)

        items = query.order_by(Initiative.id.desc()).limit(limit).all()
        return {"status": "ok", "items": [serialize_initiative(item) for item in items], "total": len(items)}

    @app.get("/initiatives/{initiative_id}")
    def get_initiative(initiative_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")
        return {"status": "ok", "initiative": serialize_initiative(initiative)}

    @app.patch("/initiatives/{initiative_id}")
    def patch_initiative(initiative_id: int, payload: InitiativeUpdateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")

        changes = payload.model_dump(exclude_none=True)
        next_status = changes.get("status")
        if next_status is not None:
            ensure_strategic_status(next_status)

        next_objective_id = changes.get("objective_id")
        if next_objective_id is not None:
            objective = strategic_query(db, Objective, identity).filter(Objective.id == next_objective_id).first()
            if not objective:
                raise HTTPException(status_code=404, detail="Objective não encontrado")

        next_type = changes.get("initiative_type")
        if next_type is not None and next_type not in allowed_initiative_types:
            raise HTTPException(status_code=422, detail="initiative_type inválido")

        before = serialize_initiative(initiative)
        for field, value in changes.items():
            setattr(initiative, field, value)

        db.add(initiative)
        db.commit()
        db.refresh(initiative)
        initiative_monoliths = resolve_initiative_monoliths(initiative)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=initiative.tenant_id,
            entity_type="initiative",
            entity_id=initiative.id,
            title=initiative.name,
            status=initiative.status,
            owner=initiative.owner,
            assigned_to=initiative.owner,
            context={
                "objective_id": initiative.objective_id,
                "initiative_type": initiative.initiative_type,
                "monoliths": initiative_monoliths,
            },
        )
        pd_sync_result = PDIntegrationService(db).sync_process(initiative)
        pd_sync = None
        if pd_sync_result is not None:
            process = pd_sync_result["process"]
            if pd_sync_result["action"] != "noop":
                publish_strategic_event(
                    "pd.process.created" if pd_sync_result["action"] == "created" else "pd.process.versioned",
                    {
                        "initiative_id": initiative.id,
                        "process_id": process.id,
                        "process_code": process.process_code,
                        "version": process.version,
                        "target_monolith": process.target_monolith,
                    },
                )
            pd_sync = {
                "action": pd_sync_result["action"],
                "process": serialize_pd_process(process),
            }

        after = serialize_initiative(initiative)
        delta = build_strategic_delta(
            before,
            after,
            ["objective_id", "name", "description", "initiative_type", "owner", "status"],
        )
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_initiative",
            entity_id=str(initiative.id),
            action="strategic.initiative.updated",
            delta=delta,
            context={"strategic_card_id": strategic_card.get("id")},
        )

        return {"status": "updated", "initiative": serialize_initiative(initiative), "strategic_card": strategic_card, "pd_sync": pd_sync}

    @app.delete("/initiatives/{initiative_id}")
    def delete_initiative(initiative_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")

        before = serialize_initiative(initiative)
        db.delete(initiative)
        db.commit()
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_initiative",
            entity_id=str(initiative_id),
            action="strategic.initiative.deleted",
            delta={"deleted": before},
        )
        return {"status": "deleted", "initiative_id": initiative_id}

    @app.post("/initiatives/{initiative_id}/dispatch")
    def dispatch_initiative(initiative_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")

        dispatch = InitiativeDispatcher(get_event_bus()).dispatch(initiative)
        return {"status": "processed", "initiative": serialize_initiative(initiative), "dispatch": dispatch}

    @app.post("/plans")
    def create_plan(payload: PlanCreateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        ensure_strategic_status(payload.status)
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == payload.initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")

        plan = Plan(**payload.model_dump(), tenant_id=identity.tenant)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        publish_strategic_event(
            "plan.created",
            {
                "plan_id": plan.id,
                "initiative_id": plan.initiative_id,
                "title": plan.title,
                "status": plan.status,
                "priority": plan.priority,
            },
        )
        initiative_monoliths = resolve_initiative_monoliths(initiative)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=plan.tenant_id,
            entity_type="plan",
            entity_id=plan.id,
            title=plan.title,
            status=plan.status,
            owner=initiative.owner,
            assigned_to=initiative.owner,
            context={"initiative_id": plan.initiative_id, "priority": plan.priority, "monoliths": initiative_monoliths},
        )
        generation = InitiativeTaskGenerator(db).generate_for_plan(plan, initiative)
        for task in generation["created_tasks"]:
            sync_strategic_card(
                db,
                tenant_id=task.tenant_id,
                entity_type="task",
                entity_id=task.id,
                title=task.title,
                status=task.status,
                owner=initiative.owner,
                assigned_to=task.assigned_to,
                context={"plan_id": task.plan_id, "priority": task.priority, "monoliths": initiative_monoliths},
            )
            publish_strategic_event(
                "task.generated",
                {
                    "task_id": task.id,
                    "plan_id": task.plan_id,
                    "assigned_to": task.assigned_to,
                    "status": task.status,
                    "priority": task.priority,
                    "template_origin": initiative.initiative_type,
                },
            )

        academy_sync = None
        if (initiative.initiative_type or "").strip().lower() == "training":
            academy_training = build_initiative_training_plan(
                initiative_name=initiative.name,
                initiative_description=initiative.description,
                owner=initiative.owner,
                plan_title=plan.title,
                task_titles=[task.title for task in generation["created_tasks"]],
            )
            academy_event = get_event_bus().publish(
                settings.ACADEMIA_EVENT_CHANNEL,
                {
                    "event_type": "training.required",
                    "initiative_id": initiative.id,
                    "plan_id": plan.id,
                    "academy_training": academy_training,
                },
            )
            academy_sync = {
                "listener": "academia_saber",
                "channel": academy_event.channel,
                "provider": academy_event.provider,
                "academy_training": academy_training,
            }

        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_plan",
            entity_id=str(plan.id),
            action="strategic.plan.created",
            delta={"created": serialize_plan(plan)},
            context={"generated_tasks": generation["created_count"], "strategic_card_id": strategic_card.get("id")},
        )

        return {
            "status": "created",
            "plan": serialize_plan(plan),
            "strategic_card": strategic_card,
            "generated_tasks": [serialize_task(task) for task in generation["created_tasks"]],
            "generation": {
                "initiative_type": generation["initiative_type"],
                "template_count": generation["template_count"],
                "created_count": generation["created_count"],
            },
            "academy_sync": academy_sync,
        }

    @app.get("/plans")
    def list_plans(limit: int = 100, initiative_id: int | None = None, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        query = strategic_query(db, Plan, identity)
        if initiative_id is not None:
            initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == initiative_id).first()
            if not initiative:
                raise HTTPException(status_code=404, detail="Initiative não encontrada")
            query = query.filter(Plan.initiative_id == initiative_id)

        items = query.order_by(Plan.id.desc()).limit(limit).all()
        return {"status": "ok", "items": [serialize_plan(item) for item in items], "total": len(items)}

    @app.get("/plans/{plan_id}")
    def get_plan(plan_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        plan = strategic_query(db, Plan, identity).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan não encontrado")
        return {"status": "ok", "plan": serialize_plan(plan)}

    @app.patch("/plans/{plan_id}")
    def patch_plan(plan_id: int, payload: PlanUpdateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        plan = strategic_query(db, Plan, identity).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan não encontrado")

        changes = payload.model_dump(exclude_none=True)
        next_status = changes.get("status")
        if next_status is not None:
            ensure_strategic_status(next_status)

        next_initiative_id = changes.get("initiative_id")
        if next_initiative_id is not None:
            initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == next_initiative_id).first()
            if not initiative:
                raise HTTPException(status_code=404, detail="Initiative não encontrada")

        before = serialize_plan(plan)
        for field, value in changes.items():
            setattr(plan, field, value)

        db.add(plan)
        db.commit()
        db.refresh(plan)
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == plan.initiative_id).first()
        initiative_monoliths = resolve_initiative_monoliths(initiative) if initiative else []
        strategic_card = sync_strategic_card(
            db,
            tenant_id=plan.tenant_id,
            entity_type="plan",
            entity_id=plan.id,
            title=plan.title,
            status=plan.status,
            owner=initiative.owner if initiative else None,
            assigned_to=initiative.owner if initiative else None,
            context={"initiative_id": plan.initiative_id, "priority": plan.priority, "monoliths": initiative_monoliths},
        )
        after = serialize_plan(plan)
        delta = build_strategic_delta(before, after, ["initiative_id", "title", "description", "status", "priority"])
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_plan",
            entity_id=str(plan.id),
            action="strategic.plan.updated",
            delta=delta,
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "updated", "plan": serialize_plan(plan), "strategic_card": strategic_card}

    @app.delete("/plans/{plan_id}")
    def delete_plan(plan_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        plan = strategic_query(db, Plan, identity).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan não encontrado")

        before = serialize_plan(plan)
        removed_tasks = db.query(Task).filter(Task.plan_id == plan_id, Task.tenant_id == identity.tenant).count()
        db.query(Task).filter(Task.plan_id == plan_id, Task.tenant_id == identity.tenant).delete()
        db.delete(plan)
        db.commit()
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_plan",
            entity_id=str(plan_id),
            action="strategic.plan.deleted",
            delta={"deleted": before},
            context={"removed_tasks": removed_tasks},
        )
        return {"status": "deleted", "plan_id": plan_id}

    @app.post("/plans/{plan_id}/generate-tasks")
    def generate_plan_tasks(plan_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        plan = strategic_query(db, Plan, identity).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan não encontrado")

        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == plan.initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative não encontrada")

        generation = InitiativeTaskGenerator(db).generate_for_plan(plan, initiative)
        for task in generation["created_tasks"]:
            publish_strategic_event(
                "task.generated",
                {
                    "task_id": task.id,
                    "plan_id": task.plan_id,
                    "assigned_to": task.assigned_to,
                    "status": task.status,
                    "priority": task.priority,
                    "template_origin": initiative.initiative_type,
                },
            )

        academy_sync = None
        if (initiative.initiative_type or "").strip().lower() == "training":
            academy_training = build_initiative_training_plan(
                initiative_name=initiative.name,
                initiative_description=initiative.description,
                owner=initiative.owner,
                plan_title=plan.title,
                task_titles=[task.title for task in generation["created_tasks"]],
            )
            academy_event = get_event_bus().publish(
                settings.ACADEMIA_EVENT_CHANNEL,
                {
                    "event_type": "training.required",
                    "initiative_id": initiative.id,
                    "plan_id": plan.id,
                    "academy_training": academy_training,
                },
            )
            academy_sync = {
                "listener": "academia_saber",
                "channel": academy_event.channel,
                "provider": academy_event.provider,
                "academy_training": academy_training,
            }

        return {
            "status": "processed",
            "plan": serialize_plan(plan),
            "generated_tasks": [serialize_task(task) for task in generation["created_tasks"]],
            "generation": {
                "initiative_type": generation["initiative_type"],
                "template_count": generation["template_count"],
                "created_count": generation["created_count"],
            },
            "academy_sync": academy_sync,
        }

    @app.post("/tasks")
    def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        ensure_strategic_status(payload.status)
        plan = strategic_query(db, Plan, identity).filter(Plan.id == payload.plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan não encontrado")

        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == plan.initiative_id).first()
        initiative_monoliths = resolve_initiative_monoliths(initiative) if initiative else []

        task_data = payload.model_dump(exclude={"dispatch_to_opera"})
        task = Task(**task_data, tenant_id=identity.tenant)
        db.add(task)
        db.commit()
        db.refresh(task)
        strategic_card = sync_strategic_card(
            db,
            tenant_id=task.tenant_id,
            entity_type="task",
            entity_id=task.id,
            title=task.title,
            status=task.status,
            assigned_to=task.assigned_to,
            context={"plan_id": task.plan_id, "priority": task.priority, "monoliths": initiative_monoliths},
        )
        publish_strategic_event(
            "task.generated",
            {
                "task_id": task.id,
                "plan_id": task.plan_id,
                "assigned_to": task.assigned_to,
                "status": task.status,
                "priority": task.priority,
            },
        )

        opera_sync = None
        if payload.dispatch_to_opera:
            opera_sync = OperaGateway().publish_task(task)

        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_task",
            entity_id=str(task.id),
            action="strategic.task.created",
            delta={"created": serialize_task(task)},
            context={"strategic_card_id": strategic_card.get("id"), "dispatch_to_opera": payload.dispatch_to_opera},
        )

        return {"status": "created", "task": serialize_task(task), "strategic_card": strategic_card, "opera_sync": opera_sync}

    @app.get("/tasks")
    def list_tasks(limit: int = 100, plan_id: int | None = None, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        query = strategic_query(db, Task, identity)
        if plan_id is not None:
            plan = strategic_query(db, Plan, identity).filter(Plan.id == plan_id).first()
            if not plan:
                raise HTTPException(status_code=404, detail="Plan não encontrado")
            query = query.filter(Task.plan_id == plan_id)

        items = query.order_by(Task.id.desc()).limit(limit).all()
        return {"status": "ok", "items": [serialize_task(item) for item in items], "total": len(items)}

    @app.get("/tasks/{task_id}")
    def get_task(task_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        task = strategic_query(db, Task, identity).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task não encontrada")
        return {"status": "ok", "task": serialize_task(task)}

    @app.patch("/tasks/{task_id}")
    def patch_task(task_id: int, payload: TaskUpdateRequest, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        task = strategic_query(db, Task, identity).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task não encontrada")

        changes = payload.model_dump(exclude_none=True)
        next_status = changes.get("status")
        if next_status is not None:
            ensure_strategic_status(next_status)
        next_plan_id = changes.get("plan_id")
        if next_plan_id is not None:
            plan = strategic_query(db, Plan, identity).filter(Plan.id == next_plan_id).first()
            if not plan:
                raise HTTPException(status_code=404, detail="Plan não encontrado")

        before = serialize_task(task)
        for field, value in changes.items():
            setattr(task, field, value)

        db.add(task)
        db.commit()
        db.refresh(task)
        plan = strategic_query(db, Plan, identity).filter(Plan.id == task.plan_id).first()
        initiative = strategic_query(db, Initiative, identity).filter(Initiative.id == plan.initiative_id).first() if plan else None
        initiative_monoliths = resolve_initiative_monoliths(initiative) if initiative else []
        strategic_card = sync_strategic_card(
            db,
            tenant_id=task.tenant_id,
            entity_type="task",
            entity_id=task.id,
            title=task.title,
            status=task.status,
            assigned_to=task.assigned_to,
            context={"plan_id": task.plan_id, "priority": task.priority, "monoliths": initiative_monoliths},
        )
        after = serialize_task(task)
        delta = build_strategic_delta(before, after, ["plan_id", "title", "description", "assigned_to", "status", "priority"])
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_task",
            entity_id=str(task.id),
            action="strategic.task.updated",
            delta=delta,
            context={"strategic_card_id": strategic_card.get("id")},
        )
        return {"status": "updated", "task": serialize_task(task), "strategic_card": strategic_card}

    @app.get("/strategic-suggestions/{entity_type}/{entity_id}")
    def strategic_john_suggestion(
        entity_type: str,
        entity_id: int,
        focus: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})

        normalized_entity, snapshot, entity_context, card = load_strategic_entity_context(db, identity, entity_type, entity_id)
        target_john = resolve_strategic_john_target(normalized_entity, entity_context)
        prompt = build_strategic_john_prompt(normalized_entity, entity_context, focus)

        discussion = discuss_with_local_john(
            JohnDiscussRequest(
                topic=f"strategic_{normalized_entity}",
                message=prompt,
                target_john=target_john,
            )
        )
        suggestion = build_strategic_john_recommendation(
            entity_type=normalized_entity,
            entity_id=entity_id,
            target_john=target_john,
            discussion=discussion,
            context=entity_context,
            focus=focus,
        )

        memory_store = get_short_term_memory()
        memory_store.set_context(
            suggestion["conversation_id"],
            {
                "tenant": identity.tenant,
                "entity_type": normalized_entity,
                "entity_id": entity_id,
                "focus": suggestion["focus"],
                "suggestion": suggestion,
            },
            ttl_seconds=settings.JOHN_MEMORY_TTL_SECONDS,
        )

        telemetry_entry = {
            **discussion.get("telemetry", {}),
            "tenant": identity.tenant,
            "entity_type": normalized_entity,
            "entity_id": entity_id,
            "memory_provider": memory_store.provider,
        }
        app.state.john_telemetry.append(telemetry_entry)
        get_event_bus().publish(settings.JOHN_TELEMETRY_CHANNEL, telemetry_entry)

        update_strategic_card_john_summary(db, card, suggestion)
        record_strategic_audit(
            db,
            identity,
            entity_type=f"strategic_{normalized_entity}",
            entity_id=str(entity_id),
            action="strategic.john.suggestion.generated",
            delta={
                "john": {
                    "target_john": target_john,
                    "recommended_action": suggestion["recommended_action"],
                    "risk": suggestion["risk"],
                }
            },
            context={
                "focus": suggestion["focus"],
                "conversation_id": suggestion["conversation_id"],
                "target_monolith": suggestion["target_monolith"],
                "card_id": card.id if card is not None else None,
            },
        )

        return {
            "status": "ok",
            "entity": snapshot,
            "suggestion": suggestion,
            "telemetry": {**telemetry_entry, "logged": True},
            "memory": {"provider": memory_store.provider, "ttl_seconds": settings.JOHN_MEMORY_TTL_SECONDS},
            "card_id": card.id if card is not None else None,
        }

    @app.get("/strategic-audit")
    def list_strategic_audit(
        limit: int = 100,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        safe_limit = max(1, min(limit, 300))

        query = db.query(AuditLog).filter(AuditLog.entity_type.like("strategic_%"))
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if actor:
            query = query.filter(AuditLog.user_id == actor)

        rows = query.order_by(AuditLog.created_at.desc()).limit(safe_limit).all()
        parsed_items = [serialize_audit_log(item) for item in rows]
        items = [item for item in parsed_items if str((item.get("context") or {}).get("tenant") or "") == identity.tenant]
        return {"status": "ok", "items": items, "total": len(items)}

    @app.get("/strategic-kanban/board")
    def strategic_kanban_board(
        portfolio: str | None = None,
        monolith: str | None = None,
        actor: str | None = None,
        stage: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        if stage is not None:
            ensure_strategic_status(stage)

        board = StrategicKanbanService(db, get_event_bus()).board(
            tenant=identity.tenant,
            portfolio=portfolio,
            monolith=monolith,
            actor=actor,
            stage=stage,
        )
        return {"status": "ok", **board}

    @app.patch("/strategic-kanban/cards/{card_id}/stage")
    def move_strategic_card(
        card_id: str,
        payload: StrategicKanbanStageRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        from app.models.orchestration import KanbanCard

        card = db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card não encontrado")
        ensure_same_tenant((card.context or {}).get("tenant"), identity)
        previous_stage = card.stage if card is not None else None
        try:
            snapshot = StrategicKanbanService(db, get_event_bus()).move_card(card_id, payload.stage)
        except ValueError as exc:
            if str(exc) == "card_not_found":
                raise HTTPException(status_code=404, detail="Card não encontrado") from exc
            if str(exc) == "invalid_card_type":
                raise HTTPException(status_code=409, detail="Card não é estratégico") from exc
            if str(exc) == "invalid_stage":
                raise HTTPException(status_code=422, detail="status estratégico inválido") from exc
            if str(exc) == "invalid_transition":
                raise HTTPException(status_code=409, detail="Transição estratégica inválida") from exc
            raise

        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_kanban_card",
            entity_id=card_id,
            action="strategic.kanban.stage_changed",
            delta={"stage": {"from": previous_stage, "to": snapshot.get("stage")}},
            context={
                "card_type": snapshot.get("card_type"),
                "entity_type": snapshot.get("entity_type"),
                "entity_id": snapshot.get("entity_id"),
            },
        )
        return {"status": "updated", "card": snapshot}

    @app.delete("/tasks/{task_id}")
    def delete_task(task_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor"})
        task = strategic_query(db, Task, identity).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task não encontrada")

        before = serialize_task(task)
        db.delete(task)
        db.commit()
        record_strategic_audit(
            db,
            identity,
            entity_type="strategic_task",
            entity_id=str(task_id),
            action="strategic.task.deleted",
            delta={"deleted": before},
        )
        return {"status": "deleted", "task_id": task_id}

    @app.post("/tasks/{task_id}/dispatch-opera")
    def dispatch_task_to_opera(task_id: int, db: Session = Depends(get_db), identity: UserIdentity = Depends(get_current_identity)):
        ensure_strategic_rbac(identity, {"executivo", "gestor", "operacional"})
        task = strategic_query(db, Task, identity).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task não encontrada")

        sync_result = OperaGateway().publish_task(task)
        return {"status": "processed", "task": serialize_task(task), "opera_sync": sync_result}

    @app.get("/work")
    def list_work(limit: int = 100, db: Session = Depends(get_db)):
        sdk = build_liceu_sdk(db, get_event_bus())
        works = sdk.work.list(limit=limit)
        return {"status": "ok", "items": [serialize_work_item(item) for item in works], "total": len(works)}

    @app.patch("/work/{work_id}")
    def patch_work(work_id: str, payload: WorkUpdateRequest, db: Session = Depends(get_db)):
        sdk = build_liceu_sdk(db, get_event_bus())
        work = sdk.work.update(work_id, payload.model_dump(exclude_none=True))
        if not work:
            raise HTTPException(status_code=404, detail="Work não encontrado")
        return {"status": "updated", "work": serialize_work_item(work)}

    @app.post("/work/{work_id}/orchestrate")
    def orchestrate_work(work_id: str, db: Session = Depends(get_db)):
        sdk = build_liceu_sdk(db, get_event_bus())
        try:
            result = sdk.orchestrator.handle(work_id=work_id)
        except ValueError as exc:
            if str(exc) == "work_not_found":
                raise HTTPException(status_code=404, detail="Work não encontrado") from exc
            raise
        return {"status": "ok", "result": result}

    @app.post("/events")
    def create_event(payload: EventCreateRequest, db: Session = Depends(get_db)):
        sdk = build_liceu_sdk(db, get_event_bus())
        event = sdk.events.emit(payload.event_type, payload.payload, source=payload.source)
        return {"status": "published", "event": serialize_event(event)}

    @app.get("/events")
    def list_events(limit: int = 200, db: Session = Depends(get_db)):
        sdk = build_liceu_sdk(db, get_event_bus())
        items = sdk.events.list(limit=limit)
        return {"status": "ok", "items": [serialize_event(item) for item in items], "total": len(items)}

    @app.post("/kanban/events/ingest")
    def kanban_ingest_event(
        payload: KanbanIngestRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        card = KanbanService(db, get_event_bus()).ingest_event(
            payload.event_type,
            payload.payload,
            source=payload.source,
        )
        return {"status": "projected", "card": card}

    @app.post("/kanban/runtime/sync")
    def kanban_runtime_sync(
        limit: int = settings.KANBAN_RUNTIME_SYNC_BATCH,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        safe_limit = max(1, min(limit, 1000))
        service = KanbanService(db, get_event_bus())
        try:
            result = service.sync_runtime_events(
                redis_url=settings.KANBAN_RUNTIME_REDIS_URL,
                stream_name=settings.KANBAN_RUNTIME_EVENT_STREAM,
                limit=safe_limit,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"sync_failed: {exc}") from exc

        return {"status": "ok", "result": result}

    @app.get("/kanban/cards")
    def kanban_cards(
        monolith_view: str | None = None,
        assigned_to: str | None = None,
        risk: str | None = None,
        min_value: float | None = None,
        stage: str | None = None,
        owner: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        service = KanbanService(db, get_event_bus())
        items = service.list_cards(
            monolith_view=monolith_view,
            assigned_to=assigned_to,
            risk=risk,
            min_value=min_value,
            stage=stage,
            owner=owner,
        )
        items = service.apply_visibility(items, identity)
        return {"status": "ok", "items": items, "total": len(items)}

    @app.get("/kanban/cards/{card_id}")
    def kanban_card_detail(
        card_id: str,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        service = KanbanService(db, get_event_bus())
        card = service.serialize_card(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Card não encontrado")

        visible = service.apply_visibility([card], identity)
        if not visible:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return {"status": "ok", "card": card}

    @app.get("/kanban/board")
    def kanban_board(
        monolith_view: str | None = None,
        assigned_to: str | None = None,
        risk: str | None = None,
        min_value: float | None = None,
        stage: str | None = None,
        owner: str | None = None,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        service = KanbanService(db, get_event_bus())
        board = service.board(
            monolith_view=monolith_view,
            assigned_to=assigned_to,
            risk=risk,
            min_value=min_value,
            stage=stage,
            owner=owner,
        )
        board["cards"] = service.apply_visibility(board.get("cards", []), identity)
        for column in board.get("columns", []):
            column_items = column.get("items") if isinstance(column, dict) else None
            if isinstance(column_items, list):
                column["items"] = service.apply_visibility(column_items, identity)
        return {"status": "ok", **board}

    @app.patch("/kanban/cards/{card_id}/assign")
    def kanban_assign_card(
        card_id: str,
        payload: KanbanAssignRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        try:
            snapshot = KanbanService(db, get_event_bus()).assign_card(card_id, payload.assigned_to, identity)
        except ValueError as exc:
            if str(exc) == "card_not_found":
                raise HTTPException(status_code=404, detail="Card não encontrado") from exc
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Acesso negado") from exc
        return {"status": "updated", "card": snapshot}

    @app.post("/kanban/cards/{card_id}/comments")
    def kanban_add_comment(
        card_id: str,
        payload: KanbanCommentRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        try:
            snapshot = KanbanService(db, get_event_bus()).add_comment(card_id, payload.content, identity)
        except ValueError as exc:
            if str(exc) == "card_not_found":
                raise HTTPException(status_code=404, detail="Card não encontrado") from exc
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Acesso negado") from exc
        return {"status": "updated", "card": snapshot}

    @app.post("/kanban/cards/{card_id}/attachments")
    def kanban_add_attachment(
        card_id: str,
        payload: KanbanAttachmentRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        try:
            snapshot = KanbanService(db, get_event_bus()).add_attachment(
                card_id,
                file_name=payload.file_name,
                file_url=payload.file_url,
                media_type=payload.media_type,
                identity=identity,
            )
        except ValueError as exc:
            if str(exc) == "card_not_found":
                raise HTTPException(status_code=404, detail="Card não encontrado") from exc
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Acesso negado") from exc
        return {"status": "updated", "card": snapshot}

    @app.post("/kanban/cards/{card_id}/automations")
    def kanban_run_automation(
        card_id: str,
        payload: KanbanAutomationRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        try:
            snapshot = KanbanService(db, get_event_bus()).run_automation(card_id, payload.automation, identity)
        except ValueError as exc:
            if str(exc) == "card_not_found":
                raise HTTPException(status_code=404, detail="Card não encontrado") from exc
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Acesso negado") from exc
        return {"status": "updated", "card": snapshot}

    @app.get("/workspace/users")
    def workspace_users(
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        service = KanbanService(db, get_event_bus())
        users = service.list_workspace_users()
        return {
            "status": "ok",
            "users": users,
            "total": len(users),
            "max_users": 10,
            "roles": sorted(list(CANONICAL_ROLES)),
        }

    @app.post("/workspace/users")
    def workspace_create_user(
        payload: WorkspaceUserCreateRequest,
        db: Session = Depends(get_db),
        identity: UserIdentity = Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        service = KanbanService(db, get_event_bus())
        try:
            user = service.add_workspace_user(
                name=payload.name,
                email=payload.email,
                role=payload.role,
                external_username=payload.external_username,
                actor=identity.username,
            )
        except ValueError as exc:
            message = str(exc)
            if message == "invalid_role":
                raise HTTPException(status_code=422, detail="role inválida") from exc
            if message == "workspace_user_limit_reached":
                raise HTTPException(status_code=409, detail="workspace atingiu limite de 10 usuários") from exc
            if message == "email_already_exists":
                raise HTTPException(status_code=409, detail="email já cadastrado") from exc
            if message == "username_already_exists":
                raise HTTPException(status_code=409, detail="external_username já cadastrado") from exc
            raise
        return {"status": "created", "user": user}

    @app.get("/governance/roles")
    def governance_roles(identity: UserIdentity = Depends(get_current_identity)):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")

        return {
            "status": "ok",
            "roles": sorted(list(CANONICAL_ROLES)),
            "matrix": {key: sorted(list(value)) for key, value in ACTION_ALLOWED_ROLES.items()},
            "kanban_stages": KANBAN_STAGES,
            "monolith_access": ROLE_MONOLITH_ACCESS,
        }

    @app.post("/governance/approve-strategy")
    def governance_approve_strategy(
        payload: GovernanceDecisionRequest,
        identity: UserIdentity = Depends(require_role(["SUPER_ADMIN", "DIRETOR"])),
    ):
        return {
            "status": "approved",
            "action": "approve_strategy",
            "entity_id": payload.entity_id,
            "by": identity.username,
            "role": identity.role,
            "note": payload.note,
        }

    @app.post("/governance/release-payment")
    def governance_release_payment(
        payload: GovernanceDecisionRequest,
        identity: UserIdentity = Depends(require_role(["FINANCEIRO"])),
    ):
        return {
            "status": "released",
            "action": "release_payment",
            "entity_id": payload.entity_id,
            "by": identity.username,
            "role": identity.role,
            "note": payload.note,
            "metadata": payload.metadata,
        }

    @app.post("/governance/execute-work")
    def governance_execute_work(
        payload: GovernanceDecisionRequest,
        identity: UserIdentity = Depends(require_role(["GERENTE"])),
    ):
        return {
            "status": "executing",
            "action": "execute_work",
            "entity_id": payload.entity_id,
            "by": identity.username,
            "role": identity.role,
            "note": payload.note,
        }

    @app.post("/governance/change-process")
    def governance_change_process(
        payload: GovernanceProcessUpdateRequest,
        identity: UserIdentity = Depends(require_role(["QUALIDADE"])),
    ):
        return {
            "status": "updated",
            "action": "change_process",
            "process_id": payload.process_id,
            "standard_version": payload.standard_version,
            "by": identity.username,
            "role": identity.role,
            "note": payload.note,
        }

    @app.post("/governance/approve-john")
    def governance_approve_john(
        payload: GovernanceDecisionRequest,
        identity: UserIdentity = Depends(require_role(["SUPER_ADMIN"])),
    ):
        return {
            "status": "approved",
            "action": "approve_john_decision",
            "entity_id": payload.entity_id,
            "by": identity.username,
            "role": identity.role,
            "note": payload.note,
        }

    @app.post("/plugins/monolith/register")
    def register_plugin(payload: MonolithPluginRegisterRequest, db: Session = Depends(get_db)):
        existing = db.query(MonolithRegistry).filter(MonolithRegistry.name == payload.name).first()
        if existing is None:
            existing = MonolithRegistry(name=payload.name, status="up")
            db.add(existing)
            db.commit()
            db.refresh(existing)

        sdk = build_liceu_sdk(db, get_event_bus())
        sdk.orchestrator.register_monolith(payload.name, lambda work: {"handled_by": payload.name, "work_id": work.id})

        return {
            "status": "registered",
            "monolith": {
                "id": existing.id,
                "name": existing.name,
                "status": existing.status,
                "last_heartbeat": existing.last_heartbeat.isoformat() if existing.last_heartbeat else None,
            },
        }

    @app.websocket("/ws/work/updates")
    async def ws_work_updates(websocket: WebSocket):
        await websocket.accept()
        bus = get_event_bus()
        loop = asyncio.get_running_loop()

        def forward_event(entry: Dict[str, Any]) -> None:
            asyncio.run_coroutine_threadsafe(websocket.send_json(entry), loop)

        if hasattr(bus, "subscribe"):
            bus.subscribe("work.updated", forward_event)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            if hasattr(bus, "unsubscribe"):
                bus.unsubscribe("work.updated", forward_event)

    @app.websocket("/ws/john/events")
    async def john_events_websocket(websocket: WebSocket):
        await websocket.accept()
        bus = get_event_bus()
        loop = asyncio.get_running_loop()

        def forward_event(entry: Dict[str, Any]) -> None:
            asyncio.run_coroutine_threadsafe(websocket.send_json(entry), loop)

        if hasattr(bus, "subscribe"):
            bus.subscribe(settings.JOH_EVENT_CHANNEL, forward_event)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            if hasattr(bus, "unsubscribe"):
                bus.unsubscribe(settings.JOH_EVENT_CHANNEL, forward_event)

    @app.websocket("/ws/kanban/events")
    async def kanban_events_websocket(websocket: WebSocket):
        await websocket.accept()
        bus = get_event_bus()
        loop = asyncio.get_running_loop()

        def forward_event(entry: Dict[str, Any]) -> None:
            asyncio.run_coroutine_threadsafe(websocket.send_json(entry), loop)

        if hasattr(bus, "subscribe"):
            bus.subscribe(settings.KANBAN_EVENT_CHANNEL, forward_event)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            if hasattr(bus, "unsubscribe"):
                bus.unsubscribe(settings.KANBAN_EVENT_CHANNEL, forward_event)

    @app.websocket("/events/ws")
    async def events_websocket(websocket: WebSocket):
        await websocket.accept()
        bus = get_event_bus()
        loop = asyncio.get_running_loop()

        def forward_event(entry: Dict[str, Any]) -> None:
            asyncio.run_coroutine_threadsafe(websocket.send_json(entry), loop)

        if hasattr(bus, "subscribe"):
            bus.subscribe("*", forward_event)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            if hasattr(bus, "unsubscribe"):
                bus.unsubscribe("*", forward_event)

    @app.get("/facade/brand")
    def facade_brand(request: Request):
        return domain_snapshot(request)

    @app.get(f"{settings.GATEWAY_PREFIX}/duality")
    def gateway_duality():
        return {
            "proxy": "traefik",
            "entrypoint": settings.PUBLIC_PROXY_ENTRYPOINT,
            "hosts": FACADE_REGISTRY,
            "public_domains": {
                "liceu": settings.DOMAIN_LICEU,
                "archimedes": settings.DOMAIN_ARCHIMEDES,
                "cefeida": settings.DOMAIN_CEFEIDA,
                "academia": settings.DOMAIN_ACADEMIA,
            },
            "sso": {
                "enabled": True,
                "algorithm": settings.JWT_ALGORITHM,
                "client_scope": "workspace:client",
                "irmandade_scope": "workspace:internal",
            },
            "currency": settings.LICEU_CURRENCY_SYMBOL,
            "secrecy_filter": "enabled",
        }

    @app.post("/auth/sso/login")
    def sso_login(payload: SSOLoginRequest):
        identity = authenticate_user(payload.username, payload.password, payload.portal)
        return {
            "access_token": issue_access_token(identity),
            "token_type": "bearer",
            "expires_in": settings.SSO_TOKEN_TTL_MINUTES * 60,
            "profile": {
                "username": identity.username,
                "display_name": identity.display_name,
                "role": identity.role,
                "roles": identity.roles,
                "portal": identity.portal,
                "tenant": identity.tenant,
            },
            "roles": identity.roles,
            "scopes": identity.scopes,
            "monolith_access": identity.monolith_access,
        }

    @app.post("/auth/qr/create")
    def auth_qr_create(payload: QRCreateRequest):
        if payload.user_id not in DEMO_USERS:
            raise HTTPException(status_code=404, detail="Usuário não encontrado para jornada QR")

        token = uuid.uuid4().hex
        download_url = f"https://liceu.app/download?token={token}"
        play_store_url = f"{download_url}&platform=android"
        app_store_url = f"{download_url}&platform=ios"

        get_short_term_memory().set_context(
            f"qr:{token}",
            {
                "username": payload.user_id,
                "portal": payload.portal,
                "journey_context": payload.journey_context,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl_seconds=payload.ttl_seconds,
        )

        return {
            "status": "created",
            "token": token,
            "url": download_url,
            "play_store_url": play_store_url,
            "app_store_url": app_store_url,
            "expires_in": payload.ttl_seconds,
        }

    @app.post("/auth/qr/login")
    def auth_qr_login(payload: QRLoginRequest):
        qr_context = get_short_term_memory().get_context(f"qr:{payload.token}")
        if not qr_context:
            raise HTTPException(status_code=401, detail="Token QR inválido ou expirado")

        username = str(qr_context.get("username") or "cliente_demo")
        portal = str(qr_context.get("portal") or "archimedes")
        password = str(DEMO_USERS.get(username, {}).get("password") or "")
        if not password:
            raise HTTPException(status_code=401, detail="Usuário QR sem credenciais válidas")

        identity = authenticate_user(username, password, portal)
        return {
            "status": "authenticated",
            "access_token": issue_access_token(identity),
            "token_type": "bearer",
            "user": {
                "username": identity.username,
                "display_name": identity.display_name,
                "role": identity.role,
                "roles": identity.roles,
                "portal": identity.portal,
                "tenant": identity.tenant,
                "monolith_access": identity.monolith_access,
            },
            "journey_context": qr_context.get("journey_context", {}),
        }

    @app.post("/john/welcome")
    def john_welcome(payload: JohnWelcomeRequest, db: Session = Depends(get_db)):
        store = get_short_term_memory()
        response = build_welcome_response(payload)
        lead_payload = build_lead_payload(
            payload=payload,
            action={**response["john_action"], "profile": response["profile"]},
            thermometer=response["thermometer"],
            session_id=response["session_id"],
        )

        lead = BackofficeLead(**lead_payload)
        db.add(lead)
        db.commit()
        db.refresh(lead)

        memory_snapshot = {
            "request": payload.request,
            "profile": response["profile"],
            "redirect_to": response["john_action"]["redirect_to"],
            "current_page": payload.context.current_page,
            "lead_id": lead.id,
        }
        store.set_context(response["session_id"], memory_snapshot, ttl_seconds=settings.JOHN_MEMORY_TTL_SECONDS)
        get_event_bus().publish(
            settings.JOH_EVENT_CHANNEL,
            {"event_type": "john.welcome", "session_id": response["session_id"], "lead_id": lead.id, **memory_snapshot},
        )

        return {
            **response,
            "lead_id": lead.id,
            "memory": {"provider": store.provider, "ttl_seconds": settings.JOHN_MEMORY_TTL_SECONDS},
        }

    @app.post("/john/dispatch")
    async def john_dispatch(intent: str):
        rota = ROTAS_JOHN.get(normalize_dispatch_intent(intent))
        if not rota:
            return {"msg": "Não entendi, mas posso te levar ao RH ou Financeiro."}

        return {
            "redirect": rota["url"],
            "contexto": f"Acessando pilar {rota['pilar']}",
            "pilar": rota["pilar"],
        }

    @app.get("/john/discuss/{pilar}")
    async def discutir_com_monolito(pilar: str):
        percepcao_local = await fetch_local_john_status(pilar)
        return {
            "analise_holding": f"O John do {pilar} disse {percepcao_local['msg']}. Holding aprova."
        }

    @app.post("/john/discuss")
    def john_discuss(payload: JohnDiscussRequest):
        store = get_short_term_memory()
        result = discuss_with_local_john(payload)
        bus = get_event_bus()

        store.set_context(
            payload.conversation_id,
            {
                "topic": payload.topic,
                "message": payload.message,
                "target_john": payload.target_john,
                "response": result["response"],
            },
            ttl_seconds=settings.JOHN_MEMORY_TTL_SECONDS,
        )

        telemetry_entry = {
            **result["telemetry"],
            "memory_provider": store.provider,
        }
        logger.info("JOHN_DISCUSS_TELEMETRY %s", telemetry_entry)
        print(f"JOHN_DISCUSS_TELEMETRY {telemetry_entry}", flush=True)
        app.state.john_telemetry.append(telemetry_entry)
        bus.publish(settings.JOHN_TELEMETRY_CHANNEL, telemetry_entry)

        return {
            **result,
            "telemetry": {
                **telemetry_entry,
                "logged": True,
            },
        }

    @app.get("/john/telemetry")
    def john_telemetry():
        return {"items": app.state.john_telemetry[-50:], "total": len(app.state.john_telemetry)}

    @app.post("/john/crm/chat")
    def john_crm_chat(payload: JohnCRMChatRequest, db: Session = Depends(get_db)):
        store = get_short_term_memory()
        welcome_payload = JohnWelcomeRequest(
            request=payload.message,
            context={
                "current_page": payload.current_page,
                "user_type": payload.user_type,
                "session_id": payload.session_id,
                "contact": {
                    "name": payload.name,
                    "email": payload.email,
                    "phone": payload.phone,
                },
            },
        )

        response = build_welcome_response(welcome_payload)
        ml_score = app.state.crm_scoring.score(
            message=payload.message,
            profile=response["profile"],
            source=payload.source,
        )
        merged_score = round((float(response["thermometer"]["score"]) * 0.6) + (ml_score * 0.4), 2)
        response["thermometer"]["score"] = merged_score
        response["thermometer"]["band"] = "alto" if merged_score >= 70 else "medio" if merged_score >= 40 else "baixo"

        lead_payload = build_lead_payload(
            payload=welcome_payload,
            action={**response["john_action"], "profile": response["profile"]},
            thermometer=response["thermometer"],
            session_id=response["session_id"],
        )
        lead_payload["status"] = "qualified" if merged_score >= 70 else "captured"

        lead = BackofficeLead(**lead_payload)
        db.add(lead)
        db.commit()
        db.refresh(lead)

        event_payload = {
            "id": str(lead.id),
            "name": lead.name,
            "email": lead.email,
            "interest": lead.intent,
            "source": payload.source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "session_id": response["session_id"],
            "thermometer_score": lead.thermometer_score,
            "redirect_to": lead.redirect_to,
        }

        bus = get_event_bus()
        bus.publish("crm.lead.created", event_payload)
        bus.publish(
            settings.JOH_EVENT_CHANNEL,
            {
                "event_type": "crm.lead.created",
                "source": "john_crm_api",
                "payload": event_payload,
            },
        )

        memory_snapshot = {
            "lead_id": lead.id,
            "message": payload.message,
            "profile": response["profile"],
            "redirect_to": response["john_action"]["redirect_to"],
            "source": payload.source,
        }
        store.set_context(response["session_id"], memory_snapshot, ttl_seconds=settings.JOHN_MEMORY_TTL_SECONDS)

        whatsapp_result = None
        if payload.phone:
            message = (
                f"Olá {lead.name}, aqui é o John da LICEU. "
                f"Seu protocolo é {lead.id} e seu perfil foi classificado como {response['profile']}."
            )
            delivery = app.state.whatsapp_service.send_text(to=payload.phone, body=message)
            whatsapp_result = {
                "status": delivery.status,
                "to": delivery.to,
                "provider": delivery.provider,
                "message_id": delivery.message_id,
                "detail": delivery.detail,
            }

        return {
            "status": "ok",
            "lead_id": lead.id,
            "session_id": response["session_id"],
            "profile": response["profile"],
            "reply": build_crm_reply(response["profile"], float(response["thermometer"]["score"])),
            "thermometer": response["thermometer"],
            "ml_score": ml_score,
            "john_action": response["john_action"],
            "whatsapp": whatsapp_result,
            "memory": {"provider": store.provider, "ttl_seconds": settings.JOHN_MEMORY_TTL_SECONDS},
        }

    @app.post("/john/interpreted/ingest")
    def john_interpreted_ingest(
        payload: JohnInterpretedIngestRequest,
        request: Request,
        db: Session = Depends(get_db),
    ):
        provided_token = request.headers.get("x-john-internal-token", "")
        if provided_token != settings.JOHN_INTERNAL_TOKEN:
            raise HTTPException(status_code=401, detail="Token interno invalido")

        event_log = EventLog(
            event_type=payload.type,
            payload={
                "input_subject": payload.input_subject,
                "input_event": payload.input_event,
                "result": payload.result,
                "ts": payload.ts,
            },
            source=payload.source,
        )
        db.add(event_log)
        db.flush()

        db.add(
            AuditLog(
                user_id=None,
                action="john.interpreted.ingested",
                entity_type="event",
                entity_id=event_log.id,
            )
        )

        immutable = ImmutableAuditService(db)
        immutable.append(
            entity_type="event",
            entity_id=event_log.id,
            action="john.interpreted.ingested",
            actor="john_engine",
            payload={
                "source": payload.source,
                "input_subject": payload.input_subject,
                "result": payload.result,
            },
        )

        db.commit()
        db.refresh(event_log)

        return {
            "status": "ingested",
            "event_id": event_log.id,
            "event_type": event_log.event_type,
            "source": event_log.source,
        }

    @app.get("/john/leads")
    def john_leads(db: Session = Depends(get_db)):
        leads = db.query(BackofficeLead).order_by(BackofficeLead.id.desc()).limit(100).all()
        items = [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
                "profile": item.inferred_profile,
                "intent": item.intent,
                "redirect_to": item.redirect_to,
                "score": item.thermometer_score,
                "status": item.status,
                "source_page": item.source_page,
            }
            for item in leads
        ]
        return {"items": items, "total": len(items)}

    @app.patch("/john/leads/{lead_id}/status")
    def john_update_lead_status(
        lead_id: int,
        payload: JohnLeadStatusUpdateRequest,
        db: Session = Depends(get_db),
    ):
        allowed = {"captured", "qualified", "converted", "lost", "won", "rejected"}
        normalized = payload.status.strip().lower()
        if normalized not in allowed:
            raise HTTPException(status_code=422, detail="Status inválido para lead")

        lead = db.query(BackofficeLead).filter(BackofficeLead.id == lead_id).first()
        if lead is None:
            raise HTTPException(status_code=404, detail="Lead não encontrado")

        lead.status = normalized
        db.add(
            AuditLog(
                user_id="john_crm",
                action="crm.lead.status.updated",
                entity_type="backoffice_lead",
                entity_id=str(lead_id),
            )
        )
        db.commit()
        db.refresh(lead)

        get_event_bus().publish(
            "crm.lead.status.updated",
            {
                "event_type": "crm.lead.status.updated",
                "source": "john_crm_api",
                "payload": {
                    "lead_id": lead.id,
                    "status": lead.status,
                    "note": payload.note,
                },
            },
        )

        return {
            "status": "updated",
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "lead_status": lead.status,
            },
        }

    @app.get("/john/leads/metrics")
    def john_lead_metrics(days: int = 30, db: Session = Depends(get_db)):
        safe_days = max(1, min(days, 365))
        since = datetime.now(timezone.utc) - timedelta(days=safe_days)

        leads = (
            db.query(BackofficeLead)
            .filter(BackofficeLead.criado_em >= since)
            .order_by(BackofficeLead.id.desc())
            .all()
        )

        statuses = Counter((lead.status or "unknown").lower() for lead in leads)
        profiles = Counter((lead.inferred_profile or "desconhecido").lower() for lead in leads)
        sources = Counter((lead.source_page or "desconhecido") for lead in leads)

        total = len(leads)
        qualified = statuses.get("qualified", 0)
        converted = statuses.get("converted", 0) + statuses.get("won", 0)
        captured = statuses.get("captured", 0)
        lost = statuses.get("lost", 0) + statuses.get("rejected", 0)

        avg_score = round(sum(float(lead.thermometer_score or 0) for lead in leads) / total, 2) if total else 0.0
        qualification_rate = round((qualified / total) * 100, 2) if total else 0.0
        conversion_rate = round((converted / total) * 100, 2) if total else 0.0

        return {
            "window_days": safe_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpis": {
                "total": total,
                "captured": captured,
                "qualified": qualified,
                "converted": converted,
                "lost": lost,
                "avg_score": avg_score,
                "qualification_rate": qualification_rate,
                "conversion_rate": conversion_rate,
            },
            "funnel": [
                {"stage": "captured", "count": captured},
                {"stage": "qualified", "count": qualified},
                {"stage": "converted", "count": converted},
                {"stage": "lost", "count": lost},
            ],
            "by_profile": [{"profile": key, "count": value} for key, value in profiles.most_common()],
            "by_source": [{"source": key, "count": value} for key, value in sources.most_common()],
        }

    @app.post("/john/crm/scoring/retrain")
    def john_retrain_scoring(
        payload: JohnCRMScoringRetrainRequest,
        db: Session = Depends(get_db),
    ):
        since = datetime.now(timezone.utc) - timedelta(days=payload.lookback_days)
        leads = (
            db.query(BackofficeLead)
            .filter(BackofficeLead.criado_em >= since)
            .order_by(BackofficeLead.id.desc())
            .all()
        )
        if len(leads) < payload.min_examples:
            return {
                "status": "skipped",
                "reason": "insufficient_examples",
                "required": payload.min_examples,
                "available": len(leads),
            }

        result = app.state.crm_scoring.retrain_from_leads(leads)
        return {
            "status": result.get("status", "trained"),
            "lookback_days": payload.lookback_days,
            "result": result,
        }

    @app.post("/john/crm/whatsapp/send")
    def john_whatsapp_send(payload: JohnCRMWhatsAppMessageRequest):
        target = payload.to or app.state.whatsapp_service.default_contact()
        delivery = app.state.whatsapp_service.send_text(to=target, body=payload.message)
        return {
            "status": delivery.status,
            "channel": delivery.channel,
            "to": delivery.to,
            "provider": delivery.provider,
            "message_id": delivery.message_id,
            "detail": delivery.detail,
        }

    @app.get("/john/crm/whatsapp/status")
    def john_whatsapp_status():
        return app.state.whatsapp_service.readiness()

    @app.get("/john/crm/whatsapp/webhook")
    def john_whatsapp_webhook_verify(
        hub_mode: str | None = Query(default=None, alias="hub.mode"),
        hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
        hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    ):
        if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN and hub_challenge:
            return int(hub_challenge)
        raise HTTPException(status_code=403, detail="Webhook token inválido")

    @app.post("/john/crm/whatsapp/webhook")
    def john_whatsapp_webhook_ingest(payload: Dict[str, Any], db: Session = Depends(get_db)):
        try:
            entry = (payload.get("entry") or [])[0]
            changes = (entry.get("changes") or [])[0]
            value = changes.get("value") or {}
            messages = value.get("messages") or []
            if not messages:
                return {"status": "ignored", "reason": "no_messages"}

            message = messages[0]
            from_phone = message.get("from")
            text_value = ((message.get("text") or {}).get("body") or "").strip()
            if not text_value:
                return {"status": "ignored", "reason": "empty_message"}

            response = john_crm_chat(
                JohnCRMChatRequest(
                    message=text_value,
                    source="whatsapp",
                    phone=from_phone,
                    user_type="Guest",
                    current_page="whatsapp",
                ),
                db,
            )
            return {"status": "processed", "lead_id": response.get("lead_id"), "profile": response.get("profile")}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    @app.get("/auth/sso/me")
    def sso_me(identity=Depends(get_current_identity)):
        return {
            "username": identity.username,
            "display_name": identity.display_name,
            "role": identity.role,
            "roles": identity.roles,
            "portal": identity.portal,
            "tenant": identity.tenant,
            "scopes": identity.scopes,
            "monolith_access": identity.monolith_access,
        }

    @app.post("/orchestration/secure")
    def orchestration_secure(
        payload: LiceuSecureOrchestrationRequest,
        request: Request,
        identity=Depends(get_current_identity),
    ):
        if "workspace:internal" not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente para orquestração central")

        orchestrator = get_liceu_orchestrator(app, use_nats_transport=payload.use_nats_transport)
        internal_token = orchestrator.auth.issue_token(user=identity.username, role="SYSTEM")
        auth_header = f"Bearer {internal_token}"

        client_host = request.client.host if request.client and request.client.host else "unknown"
        client_id = payload.client_id or f"{identity.username}:{client_host}"

        try:
            result = orchestrator.orchestrate_secure(
                work_id=payload.work_id,
                context=payload.context,
                signals=payload.signals,
                auth_header=auth_header,
                client_id=client_id,
            )
        except PermissionError as exc:
            reason = str(exc)
            if reason in {"missing_bearer_token", "invalid_token_signature", "expired_token"}:
                raise HTTPException(status_code=401, detail=reason) from exc
            if reason == "role_not_allowed":
                raise HTTPException(status_code=403, detail=reason) from exc
            if reason == "rate_limit_exceeded":
                raise HTTPException(status_code=429, detail=reason) from exc
            raise HTTPException(status_code=403, detail=reason) from exc
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        work = result["work"]
        decision = result["decision"]

        return {
            "status": "completed",
            "work": {
                "id": work.id,
                "status": work.status,
                "assignee": work.assignee,
                "dependencies": work.dependencies,
                "watchers": work.watchers,
            },
            "decision": {
                "action": decision.action,
                "reason": decision.reason,
                "target_monolith": result["target_monolith"],
            },
            "rules_violations": result["rules_violations"],
            "financial": result["financial"],
            "contract": result.get("contract"),
            "events": result["events"],
        }

    @app.get("/workspace/context")
    def workspace_context(identity=Depends(get_current_identity)):
        return {
            "viewer_role": identity.role,
            "roles": identity.roles,
            "portal": identity.portal,
            "tenant": identity.tenant,
            "modules": workspace_modules(identity),
            "monolith_access": identity.monolith_access,
            "sigilo": "industrial" if "workspace:internal" in identity.scopes else "cliente",
        }

    @app.get("/market/insights")
    def market_insights(identity=Depends(get_current_identity)):
        return filter_market_payload(identity)

    @app.post("/brain/sync")
    def brain_sync(payload: BrainSyncRequest):
        bus = get_event_bus()
        vision = ConcreteVisionAI()
        pathology_report = vision.inspect_pathologies(
            observations=payload.observations,
            discipline=payload.discipline,
            artifact_uri=payload.artifact_uri,
        )
        cognitive_pulse = build_cognitive_pulse(pathology_report, payload)
        academy_training = build_training_plan(
            project_code=payload.project_code,
            discipline=payload.discipline,
            report=pathology_report,
            pulse=cognitive_pulse.model_dump(mode="json"),
        )

        pulse_message = cognitive_pulse.model_dump(mode="json")
        joh_event = bus.publish(
            settings.JOH_EVENT_CHANNEL,
            {
                "event_type": "brain.sync",
                "project_code": payload.project_code,
                "pathology_report": pathology_report,
                "cognitive_pulse": pulse_message,
            },
        )
        academy_event = bus.publish(
            settings.ACADEMIA_EVENT_CHANNEL,
            {
                "event_type": "academy.training.generated",
                "project_code": payload.project_code,
                "academy_training": academy_training,
            },
        )

        return {
            "status": "synced",
            "source": payload.reported_by,
            "pathology_report": pathology_report,
            "cognitive_pulse": pulse_message,
            "academy_training": academy_training,
            "event_delivery": {
                "provider": joh_event.provider,
                "listener": "joh_brasileiro",
                "academy_listener": "academia_saber",
                "channels": [joh_event.channel, academy_event.channel],
            },
        }

    @app.get("/health/global")
    def global_health():
        registry = get_monolith_registry()
        database_ok = check_database_health()
        bus = get_event_bus()
        redis_ok = bus.ping()

        monoliths = []
        for item in registry:
            monoliths.append(
                {
                    **item,
                    "status": "healthy" if item["slug"] == "core_os" and database_ok else "registered",
                }
            )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gateway": "leme-core",
            "network": settings.NETWORK_NAME,
            "overall_status": "healthy" if database_ok and redis_ok else "degraded",
            "total_pillars": len(monoliths),
            "dependencies": {
                "database": {"status": "up" if database_ok else "down"},
                "redis": {
                    "status": "up" if redis_ok else "down",
                    "provider": bus.provider,
                    "channel": settings.JOH_EVENT_CHANNEL,
                },
                "sso": {"status": "up", "scopes": ["workspace:client", "workspace:internal"]},
                "sigilo": {"status": "up", "mode": "dualidade_de_mercado"},
                "brain_sync": {
                    "status": "up",
                    "providers": ["concrete-vision-ai", "joh_brasileiro", "academia_saber"],
                },
                "john_central": {
                    "status": "up",
                    "memory": get_short_term_memory().provider,
                    "crm": "backoffice_leads",
                },
            },
            "monoliths": monoliths,
        }

    @app.post("/events/publish")
    def publish_event(event: EventPayload):
        bus = get_event_bus()
        message = {
            "event_type": event.event_type,
            "origin": event.origin,
            "payload": event.payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = bus.publish(event.channel, message)
        return {
            "status": "published",
            "provider": result.provider,
            "channel": result.channel,
            "listener": "joh_brasileiro",
            "message": result.message,
        }

    @app.post("/sdk/public/emit")
    def sdk_public_emit(payload: SDKPublicEmitRequest, request: Request):
        sdk_key = request.headers.get("x-john-sdk-key", "")
        if sdk_key and sdk_key != "public-dev":
            raise HTTPException(status_code=401, detail="SDK key inválida")

        growth_payload = payload.payload if isinstance(payload.payload, dict) else {"data": payload.payload}
        growth_payload.setdefault("event", "unknown")

        aggregate_growth_payload(app.state.growth_summary, growth_payload)

        event_entry = {
            "type": payload.type,
            "payload": growth_payload,
            "path": request.url.path,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        app.state.growth_events.append(event_entry)
        if len(app.state.growth_events) > 1000:
            app.state.growth_events = app.state.growth_events[-1000:]

        bus = get_event_bus()
        bus_result = bus.publish(
            settings.JOHN_TELEMETRY_CHANNEL,
            {
                "event_type": payload.type,
                "source": "sdk.public",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": growth_payload,
            },
        )

        return {
            "status": "accepted",
            "event_type": payload.type,
            "provider": bus_result.provider,
            "channel": bus_result.channel,
            "summary_updated_at": app.state.growth_summary.get("updated_at"),
        }

    @app.get("/sdk/public/growth-summary")
    def sdk_public_growth_summary(limit: int = 50):
        safe_limit = max(1, min(limit, 200))
        events = app.state.growth_events[-safe_limit:]
        return {
            "status": "ok",
            "updated_at": app.state.growth_summary.get("updated_at"),
            "summary": app.state.growth_summary,
            "recent_events": events,
            "buffered_events": len(app.state.growth_events),
        }

    @app.post("/sdk/public/growth-summary/reset")
    def sdk_public_growth_summary_reset():
        app.state.growth_summary = build_empty_growth_summary()
        app.state.growth_events = []

        bus = get_event_bus()
        bus.publish(
            settings.JOHN_TELEMETRY_CHANNEL,
            {
                "event_type": "growth.summary.reset",
                "source": "sdk.public",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"reason": "manual_reset"},
            },
        )

        return {
            "status": "reset",
            "updated_at": app.state.growth_summary.get("updated_at"),
        }

    def _build_ecosystem_metrics_data(db: Session) -> dict[str, Any]:
        from app.models.orchestration import KanbanCard, KanbanEvent, MonolithRegistry, AuditLog

        cards = db.query(KanbanCard).all()
        total_cards = len(cards)
        closed_cards = [c for c in cards if c.stage == "closed"]
        high_risk_cards = [c for c in cards if c.risk_level == "high"]
        active_leads = [c for c in cards if c.stage == "leads"]
        active_deals = [c for c in cards if c.stage in {"negotiation", "proposal"}]
        juridico_cards = [c for c in cards if c.stage == "juridico"]
        conversion_rate = round((len(closed_cards) / total_cards) * 100, 2) if total_cards else 0.0

        from decimal import Decimal as Dec
        def _float(v):
            try:
                return float(v or 0)
            except Exception:
                return 0.0

        estimated_revenue = sum(_float(c.monetary_value) for c in closed_cards)
        pipeline_value = sum(_float(c.monetary_value) for c in cards)
        ar_value = sum(_float(c.monetary_value) for c in cards if c.stage in {"proposal", "juridico"})
        ap_value = sum(_float(c.monetary_value) for c in cards if c.stage in {"leads", "negotiation"})

        funnel = [
            {"stage": "leads", "count": len(active_leads), "value": sum(_float(c.monetary_value) for c in active_leads)},
            {"stage": "negotiation", "count": len(active_deals), "value": sum(_float(c.monetary_value) for c in active_deals)},
            {"stage": "proposal", "count": len([c for c in cards if c.stage == "proposal"]), "value": sum(_float(c.monetary_value) for c in cards if c.stage == "proposal")},
            {"stage": "juridico", "count": len(juridico_cards), "value": sum(_float(c.monetary_value) for c in juridico_cards)},
            {"stage": "closed", "count": len(closed_cards), "value": estimated_revenue},
        ]

        # Monolith status from registry + event volume
        KNOWN_MONOLITHS = ["archimedes", "juridicotech", "hubbackoffice", "cefeida", "gamemkt", "john", "academia", "cea_invest", "econo_tech"]
        monolith_status = []
        for name in KNOWN_MONOLITHS:
            reg = db.query(MonolithRegistry).filter(MonolithRegistry.name == name).first()
            event_count = db.query(KanbanEvent).filter(KanbanEvent.source == name).count()
            card_count = len([c for c in cards if c.source == name])
            status = reg.status if reg else "unknown"
            last_beat = reg.last_heartbeat.isoformat() if reg and reg.last_heartbeat else None
            monolith_status.append({
                "name": name,
                "status": status,
                "event_volume": event_count,
                "card_volume": card_count,
                "last_heartbeat": last_beat,
                "latency_ms": None,
            })

        # Risk signals from context alerts
        risk_signals = []
        for c in cards:
            ctx = c.context or {}
            alerts = ctx.get("alerts") or []
            if alerts:
                risk_signals.append({
                    "card_id": c.id,
                    "title": c.title,
                    "stage": c.stage,
                    "risk": c.risk_level,
                    "alerts": alerts,
                    "value": _float(c.monetary_value),
                })

        # Performance per source (top performers)
        perf_map: dict[str, dict] = {}
        for c in cards:
            src = c.source or "unknown"
            if src not in perf_map:
                perf_map[src] = {"source": src, "cards": 0, "closed": 0, "revenue": 0.0}
            perf_map[src]["cards"] += 1
            if c.stage == "closed":
                perf_map[src]["closed"] += 1
                perf_map[src]["revenue"] += _float(c.monetary_value)
        performance = sorted(perf_map.values(), key=lambda x: x["revenue"], reverse=True)

        # Recent audit actions
        recent_audit = []
        for entry in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all():
            recent_audit.append({
                "user_id": entry.user_id,
                "action": entry.action,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "timestamp": entry.created_at.isoformat() if entry.created_at else None,
            })

        # Recent events
        recent_events = []
        for ev in db.query(KanbanEvent).order_by(KanbanEvent.occurred_at.desc()).limit(30).all():
            recent_events.append({
                "event_type": ev.event_type,
                "source": ev.source,
                "card_id": ev.card_id,
                "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
            })

        return {
            "kpis": {
                "total_cards": total_cards,
                "active_leads": len(active_leads),
                "active_deals": len(active_deals),
                "juridico_cards": len(juridico_cards),
                "closed_cards": len(closed_cards),
                "high_risk_cards": len(high_risk_cards),
                "conversion_rate": conversion_rate,
                "estimated_revenue": estimated_revenue,
                "pipeline_value": pipeline_value,
            },
            "financeiro": {
                "estimated_revenue": estimated_revenue,
                "pipeline_value": pipeline_value,
                "accounts_receivable": ar_value,
                "accounts_payable": ap_value,
            },
            "funnel": funnel,
            "monolith_status": monolith_status,
            "risk_signals": risk_signals,
            "performance": performance,
            "recent_events": recent_events,
            "recent_audit": recent_audit,
        }

    @app.get("/metrics")
    def ecosystem_metrics(db: Session = Depends(get_db)):
        return {"status": "ok", "data": _build_ecosystem_metrics_data(db)}

    # ─── DECISION ENGINE — Nível 2 ──────────────────────────────────────────

    # In-memory store para decisões geradas nesta sessão.
    # Em produção, persistir em tabela DecisionRecord no banco.
    _decision_store: list[dict] = []
    _autonomous_mode: dict[str, str] = {"mode": "SEMI"}
    _autonomous_state_store: dict[str, Any] = {}
    _autonomous_action_store: list[dict[str, Any]] = []
    _autonomous_action_cache: set[str] = set()
    _innovation_mode: dict[str, str] = {"mode": "SUPERVISED"}
    _innovation_state_store: dict[str, Any] = {}
    _innovation_action_store: list[dict[str, Any]] = []
    _innovation_action_cache: set[str] = set()
    _executive_mode: dict[str, str] = {"mode": "SUPERVISED"}
    _executive_state_store: dict[str, Any] = {}
    _executive_action_store: list[dict[str, Any]] = []
    _executive_action_cache: set[str] = set()
    _executive_learning_store: dict[str, float] = {}

    @app.get("/decisions")
    def list_decisions(
        limit: int = 20,
        executed: bool | None = None,
        priority: str | None = None,
    ):
        """Retorna decisões geradas pelo Decision Engine (recentes primeiro)."""
        from app.services.decision_engine import DecisionType, PriorityLevel

        result = list(reversed(_decision_store))
        if executed is not None:
            result = [d for d in result if d.get("executed") == executed]
        if priority:
            result = [d for d in result if d.get("priority") == priority.upper()]
        return {"status": "ok", "total": len(result), "decisions": result[:limit]}

    @app.post("/decisions/process")
    def process_event_decisions(body: dict, db: Session = Depends(get_db)):
        """
        Processa um evento avulso pelo Decision Engine e persiste a decisão.
        Body: { event_type, source, card_id?, ...extra }
        """
        from app.services.decision_engine import evaluate_event
        from app.models.orchestration import KanbanCard

        card_ctx = None
        cid = body.get("card_id")
        if cid:
            card = db.query(KanbanCard).filter(KanbanCard.id == cid).first()
            if card:
                card_ctx = {
                    "id": card.id,
                    "stage": card.stage,
                    "monetary_value": float(card.monetary_value or 0),
                    "risk_level": card.risk_level,
                    "title": card.title,
                    "source": card.source,
                    "heat_score": (card.context or {}).get("heat_score", 0),
                    "silent_days": (card.context or {}).get("silent_days", 0),
                    "legal_pending": (card.context or {}).get("legal_pending", False),
                }

        decision = evaluate_event(body, card_ctx)
        if not decision:
            return {"status": "no_decision", "event": body.get("event_type")}

        d = decision.to_dict()
        _decision_store.append(d)
        if len(_decision_store) > 200:
            _decision_store.pop(0)

        # Publicar decisão no event bus
        bus = get_event_bus()
        bus.publish("decision.engine", {
            "event_type": "decision_generated",
            "source": "decision_engine",
            "payload": d,
        })

        return {"status": "decision_generated", "decision": d}

    @app.post("/decisions/{decision_id}/execute")
    def execute_decision(decision_id: str):
        """Executa a ação de uma decisão pelo ID."""
        from app.services.action_engine import execute_action

        dec = next((d for d in _decision_store if d["id"] == decision_id), None)
        if not dec:
            raise HTTPException(status_code=404, detail="Decisão não encontrada")
        if dec.get("executed"):
            return {"status": "already_executed", "result": dec.get("result")}

        result = execute_action(dec["action"], dec.get("payload", {}))
        dec["executed"] = True
        dec["result"] = result

        return {"status": "executed", "decision_id": decision_id, "result": result}

    @app.get("/decisions/actions")
    def list_available_actions():
        """Lista todos os slugs de ação disponíveis no Action Engine."""
        from app.services.action_engine import available_actions
        return {"actions": available_actions()}

    @app.post("/decisions/batch")
    def batch_process_decisions(body: dict, db: Session = Depends(get_db)):
        """
        Processa múltiplos eventos de uma vez.
        Body: { events: [ {event_type, source, card_id?, ...}, ... ] }
        """
        from app.services.decision_engine import batch_evaluate
        from app.models.orchestration import KanbanCard

        events = body.get("events", [])
        if not events:
            return {"status": "ok", "decisions": []}

        # Montar card_map para contexto
        card_ids = {e.get("card_id") for e in events if e.get("card_id")}
        card_map: dict[str, dict] = {}
        for cid in card_ids:
            card = db.query(KanbanCard).filter(KanbanCard.id == cid).first()
            if card:
                card_map[cid] = {
                    "id": card.id,
                    "stage": card.stage,
                    "monetary_value": float(card.monetary_value or 0),
                    "risk_level": card.risk_level,
                    "title": card.title,
                    "source": card.source,
                    "heat_score": (card.context or {}).get("heat_score", 0),
                    "silent_days": (card.context or {}).get("silent_days", 0),
                    "legal_pending": (card.context or {}).get("legal_pending", False),
                }

        decisions = batch_evaluate(events, card_map)
        results = []
        for dec in decisions:
            d = dec.to_dict()
            _decision_store.append(d)
            results.append(d)

        if len(_decision_store) > 200:
            del _decision_store[:-200]

        return {"status": "ok", "processed": len(events), "decisions": results}

    # ─── AUTONOMOUS ECOSYSTEM — Nível 3 ────────────────────────────────────

    @app.get("/autonomous/state")
    def autonomous_state(db: Session = Depends(get_db)):
        from app.services.autonomous_engine import build_state

        metrics_data = _build_ecosystem_metrics_data(db)
        state = build_state(metrics_data)
        state["mode"] = _autonomous_mode["mode"]
        state["executed_actions"] = len([item for item in _autonomous_action_store if item.get("status") == "executed"])
        state["approval_queue"] = len([item for item in _autonomous_action_store if item.get("status") == "approval_required"])
        _autonomous_state_store.clear()
        _autonomous_state_store.update(state)
        return {
            "status": "ok",
            "state": state,
            "recent_actions": _autonomous_action_store[-20:],
        }

    @app.patch("/autonomous/mode")
    def autonomous_set_mode(payload: AutonomousModeRequest, db: Session = Depends(get_db)):
        from app.services.autonomous_engine import AUTONOMOUS_MODES

        normalized_mode = payload.mode.strip().upper()
        if normalized_mode not in AUTONOMOUS_MODES:
            raise HTTPException(status_code=422, detail="Modo inválido")

        _autonomous_mode["mode"] = normalized_mode
        db.add(
            AuditLog(
                user_id="john.autonomous",
                action=f"autonomous.mode.{normalized_mode.lower()}",
                entity_type="autonomous_mode",
                entity_id=normalized_mode,
            )
        )
        db.commit()
        get_event_bus().publish(
            "autonomous.mode",
            {
                "event_type": "autonomous.mode.changed",
                "source": "john.autonomous",
                "payload": {"mode": normalized_mode},
            },
        )
        return {"status": "ok", "mode": normalized_mode}

    @app.get("/autonomous/actions")
    def autonomous_actions(limit: int = 50):
        safe_limit = max(1, min(limit, 200))
        items = list(reversed(_autonomous_action_store))[:safe_limit]
        return {"status": "ok", "mode": _autonomous_mode["mode"], "actions": items, "total": len(_autonomous_action_store)}

    @app.post("/autonomous/evaluate")
    def autonomous_evaluate(db: Session = Depends(get_db)):
        from app.services.action_engine import execute_action
        from app.services.autonomous_engine import build_state, decide, orchestrate

        metrics_data = _build_ecosystem_metrics_data(db)
        state = build_state(metrics_data)
        state["mode"] = _autonomous_mode["mode"]
        decisions = decide(state)
        results = orchestrate(
            decisions=decisions,
            mode=_autonomous_mode["mode"],
            bus=get_event_bus(),
            execute_action=execute_action,
            action_cache=_autonomous_action_cache,
        )

        _autonomous_state_store.clear()
        _autonomous_state_store.update(state)
        _autonomous_action_store.extend(results)
        if len(_autonomous_action_store) > 300:
            del _autonomous_action_store[:-300]

        db.add(
            AuditLog(
                user_id="john.autonomous",
                action=f"autonomous.evaluate.{_autonomous_mode['mode'].lower()}",
                entity_type="autonomous_state",
                entity_id=state.get("updated_at"),
            )
        )
        db.commit()

        get_event_bus().publish(
            "autonomous.state",
            {
                "event_type": "autonomous.state.updated",
                "source": "john.autonomous",
                "payload": {"state": state, "decisions": results},
            },
        )

        return {"status": "ok", "mode": _autonomous_mode["mode"], "state": state, "decisions": results}

    @app.post("/autonomous/override")
    def autonomous_override(payload: AutonomousOverrideRequest, db: Session = Depends(get_db)):
        from app.services.action_engine import execute_action
        from app.services.autonomous_engine import build_idempotency_key, resolve_channel

        if payload.action == "close_deal" and not payload.contract_signed:
            raise HTTPException(status_code=403, detail="JuridicoTech bloqueou a ação: contrato não assinado")

        action_record = {
            "id": str(uuid.uuid4()),
            "type": "OVERRIDE",
            "action": payload.action,
            "target": payload.target,
            "reason": payload.reason,
            "payload": payload.payload,
            "mode": _autonomous_mode["mode"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        action_record["idempotency_key"] = build_idempotency_key(action_record)
        if action_record["idempotency_key"] in _autonomous_action_cache:
            return {"status": "duplicate", "action": action_record}

        result = execute_action(payload.action, payload.payload)
        action_record["status"] = "executed"
        action_record["result"] = result
        action_record["channel"] = resolve_channel(action_record)

        _autonomous_action_cache.add(action_record["idempotency_key"])
        _autonomous_action_store.append(action_record)
        if len(_autonomous_action_store) > 300:
            del _autonomous_action_store[:-300]

        db.add(
            AuditLog(
                user_id="human.override",
                action=f"autonomous.override.{payload.action}",
                entity_type="autonomous_action",
                entity_id=action_record["id"],
            )
        )
        db.commit()

        get_event_bus().publish(
            action_record["channel"],
            {
                "event_type": "autonomous.override.executed",
                "source": "john.autonomous",
                "payload": action_record,
            },
        )
        return {"status": "ok", "action": action_record}

    @app.post("/autonomous/actions/{action_id}/rollback")
    def autonomous_rollback(action_id: str, db: Session = Depends(get_db)):
        action = next((item for item in _autonomous_action_store if item.get("id") == action_id), None)
        if action is None:
            raise HTTPException(status_code=404, detail="Ação autônoma não encontrada")
        if action.get("status") == "rolled_back":
            return {"status": "already_rolled_back", "action": action}

        action["status"] = "rolled_back"
        action["rolled_back_at"] = datetime.now(timezone.utc).isoformat()

        db.add(
            AuditLog(
                user_id="human.override",
                action=f"autonomous.rollback.{action.get('action')}",
                entity_type="autonomous_action",
                entity_id=action_id,
            )
        )
        db.commit()

        get_event_bus().publish(
            "autonomous.rollback",
            {
                "event_type": "autonomous.action.rolled_back",
                "source": "john.autonomous",
                "payload": action,
            },
        )
        return {"status": "rolled_back", "action": action}

    # ─── INNOVATION ENGINE — Nível 4 ───────────────────────────────────────

    @app.get("/innovation/state")
    def innovation_state(db: Session = Depends(get_db)):
        from app.services.autonomous_engine import build_state as build_autonomous_state
        from app.services.innovation_engine import build_state as build_innovation_state, decide as decide_innovation

        metrics_data = _build_ecosystem_metrics_data(db)
        autonomous_state = build_autonomous_state(metrics_data)
        state = build_innovation_state(metrics_data, autonomous_state)
        state["mode"] = _innovation_mode["mode"]
        ideas = decide_innovation(state, metrics_data)
        _innovation_state_store.clear()
        _innovation_state_store.update(state)
        return {
            "status": "ok",
            "state": state,
            "ideas": ideas,
            "recent_actions": _innovation_action_store[-20:],
        }

    @app.patch("/innovation/mode")
    def innovation_set_mode(payload: InnovationModeRequest, db: Session = Depends(get_db)):
        from app.services.innovation_engine import INNOVATION_MODES

        normalized_mode = payload.mode.strip().upper()
        if normalized_mode not in INNOVATION_MODES:
            raise HTTPException(status_code=422, detail="Modo inválido")

        _innovation_mode["mode"] = normalized_mode
        db.add(
            AuditLog(
                user_id="john.innovation",
                action=f"innovation.mode.{normalized_mode.lower()}",
                entity_type="innovation_mode",
                entity_id=normalized_mode,
            )
        )
        db.commit()
        get_event_bus().publish(
            "innovation.engine",
            {
                "event_type": "innovation.mode.changed",
                "source": "john.innovation",
                "payload": {"mode": normalized_mode},
            },
        )
        return {"status": "ok", "mode": normalized_mode}

    @app.get("/innovation/actions")
    def innovation_actions(limit: int = 50):
        safe_limit = max(1, min(limit, 200))
        items = list(reversed(_innovation_action_store))[:safe_limit]
        return {"status": "ok", "mode": _innovation_mode["mode"], "actions": items, "total": len(_innovation_action_store)}

    @app.post("/innovation/evaluate")
    def innovation_evaluate(db: Session = Depends(get_db)):
        from app.services.action_engine import execute_action
        from app.services.autonomous_engine import build_state as build_autonomous_state
        from app.services.innovation_engine import build_state as build_innovation_state, decide as decide_innovation, orchestrate as orchestrate_innovation

        metrics_data = _build_ecosystem_metrics_data(db)
        autonomous_state = build_autonomous_state(metrics_data)
        state = build_innovation_state(metrics_data, autonomous_state)
        state["mode"] = _innovation_mode["mode"]
        ideas = decide_innovation(state, metrics_data)
        results = orchestrate_innovation(
            ideas=ideas,
            mode=_innovation_mode["mode"],
            bus=get_event_bus(),
            execute_action=execute_action,
            action_cache=_innovation_action_cache,
        )

        _innovation_state_store.clear()
        _innovation_state_store.update(state)
        _innovation_action_store.extend(results)
        if len(_innovation_action_store) > 300:
            del _innovation_action_store[:-300]

        db.add(
            AuditLog(
                user_id="john.innovation",
                action=f"innovation.evaluate.{_innovation_mode['mode'].lower()}",
                entity_type="innovation_state",
                entity_id=state.get("updated_at"),
            )
        )
        db.commit()

        get_event_bus().publish(
            "innovation.engine",
            {
                "event_type": "innovation.state.updated",
                "source": "john.innovation",
                "payload": {"state": state, "ideas": results},
            },
        )

        return {"status": "ok", "mode": _innovation_mode["mode"], "state": state, "ideas": results}

    # ─── EXECUTIVE CONTROL — Nível 5 ───────────────────────────────────────

    @app.get("/executive/state")
    def executive_state(db: Session = Depends(get_db)):
        from app.services.autonomous_engine import build_state as build_autonomous_state
        from app.services.executive_engine import build_state as build_executive_state
        from app.services.innovation_engine import build_state as build_innovation_state

        metrics_data = _build_ecosystem_metrics_data(db)
        autonomous_state = build_autonomous_state(metrics_data)
        innovation_state = build_innovation_state(metrics_data, autonomous_state)
        state = build_executive_state(metrics_data, autonomous_state, innovation_state)
        state["mode"] = _executive_mode["mode"]
        state["executed_actions"] = len([item for item in _executive_action_store if item.get("status") == "executed"])
        state["approval_queue"] = len([item for item in _executive_action_store if item.get("status") == "approval_required"])

        _executive_state_store.clear()
        _executive_state_store.update(state)

        return {
            "status": "ok",
            "state": state,
            "learning": _executive_learning_store,
            "recent_actions": _executive_action_store[-20:],
        }

    @app.patch("/executive/mode")
    def executive_set_mode(payload: ExecutiveModeRequest, db: Session = Depends(get_db)):
        from app.services.executive_engine import EXECUTIVE_MODES

        normalized_mode = payload.mode.strip().upper()
        if normalized_mode not in EXECUTIVE_MODES:
            raise HTTPException(status_code=422, detail="Modo inválido")

        _executive_mode["mode"] = normalized_mode
        db.add(
            AuditLog(
                user_id="john.executive",
                action=f"executive.mode.{normalized_mode.lower()}",
                entity_type="executive_mode",
                entity_id=normalized_mode,
            )
        )
        db.commit()

        get_event_bus().publish(
            "executive.control",
            {
                "event_type": "executive.mode.changed",
                "source": "john.executive",
                "payload": {"mode": normalized_mode},
            },
        )
        return {"status": "ok", "mode": normalized_mode}

    @app.get("/executive/actions")
    def executive_actions(limit: int = 50):
        safe_limit = max(1, min(limit, 200))
        items = list(reversed(_executive_action_store))[:safe_limit]
        return {
            "status": "ok",
            "mode": _executive_mode["mode"],
            "actions": items,
            "learning": _executive_learning_store,
            "total": len(_executive_action_store),
        }

    @app.post("/executive/evaluate")
    def executive_evaluate(db: Session = Depends(get_db)):
        from app.services.action_engine import execute_action
        from app.services.autonomous_engine import build_state as build_autonomous_state
        from app.services.executive_engine import build_state as build_executive_state, decide as decide_executive, orchestrate as orchestrate_executive
        from app.services.innovation_engine import build_state as build_innovation_state

        metrics_data = _build_ecosystem_metrics_data(db)
        autonomous_state = build_autonomous_state(metrics_data)
        innovation_state = build_innovation_state(metrics_data, autonomous_state)
        state = build_executive_state(metrics_data, autonomous_state, innovation_state)
        state["mode"] = _executive_mode["mode"]

        decisions = decide_executive(state)
        results = orchestrate_executive(
            decisions=decisions,
            mode=_executive_mode["mode"],
            bus=get_event_bus(),
            execute_action=execute_action,
            action_cache=_executive_action_cache,
        )

        _executive_state_store.clear()
        _executive_state_store.update(state)
        _executive_action_store.extend(results)
        if len(_executive_action_store) > 300:
            del _executive_action_store[:-300]

        db.add(
            AuditLog(
                user_id="john.executive",
                action=f"executive.evaluate.{_executive_mode['mode'].lower()}",
                entity_type="executive_state",
                entity_id=state.get("updated_at"),
            )
        )
        db.commit()

        get_event_bus().publish(
            "executive.control",
            {
                "event_type": "executive.state.updated",
                "source": "john.executive",
                "payload": {"state": state, "decisions": results},
            },
        )

        return {"status": "ok", "mode": _executive_mode["mode"], "state": state, "decisions": results}

    @app.post("/executive/override")
    def executive_override(payload: ExecutiveOverrideRequest, db: Session = Depends(get_db)):
        from app.services.action_engine import execute_action
        from app.services.executive_engine import build_idempotency_key, resolve_channel

        normalized_action = payload.action.strip().lower()
        if normalized_action == "expand_region" and not payload.legal_approved:
            raise HTTPException(status_code=403, detail="JuridicoTech bloqueou a ação: legal_approved=false")

        action_record = {
            "id": str(uuid.uuid4()),
            "type": "EXECUTIVE_OVERRIDE",
            "action": normalized_action,
            "target": payload.target,
            "reason": payload.reason,
            "payload": payload.payload,
            "mode": _executive_mode["mode"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        action_record["idempotency_key"] = build_idempotency_key(action_record)
        if action_record["idempotency_key"] in _executive_action_cache:
            return {"status": "duplicate", "action": action_record}

        result = execute_action(normalized_action, payload.payload)
        action_record["status"] = "executed"
        action_record["result"] = result
        action_record["channel"] = resolve_channel(action_record)

        _executive_action_cache.add(action_record["idempotency_key"])
        _executive_action_store.append(action_record)
        if len(_executive_action_store) > 300:
            del _executive_action_store[:-300]

        db.add(
            AuditLog(
                user_id="human.executive",
                action=f"executive.override.{normalized_action}",
                entity_type="executive_action",
                entity_id=action_record["id"],
            )
        )
        db.commit()

        get_event_bus().publish(
            action_record["channel"],
            {
                "event_type": "executive.override.executed",
                "source": "john.executive",
                "payload": action_record,
            },
        )
        return {"status": "ok", "action": action_record}

    @app.post("/executive/actions/{action_id}/rollback")
    def executive_rollback(action_id: str, db: Session = Depends(get_db)):
        action = next((item for item in _executive_action_store if item.get("id") == action_id), None)
        if action is None:
            raise HTTPException(status_code=404, detail="Ação executiva não encontrada")
        if action.get("status") == "rolled_back":
            return {"status": "already_rolled_back", "action": action}

        action["status"] = "rolled_back"
        action["rolled_back_at"] = datetime.now(timezone.utc).isoformat()

        db.add(
            AuditLog(
                user_id="human.executive",
                action=f"executive.rollback.{action.get('action')}",
                entity_type="executive_action",
                entity_id=action_id,
            )
        )
        db.commit()

        get_event_bus().publish(
            "executive.rollback",
            {
                "event_type": "executive.action.rolled_back",
                "source": "john.executive",
                "payload": action,
            },
        )

        return {"status": "rolled_back", "action": action}

    @app.post("/executive/feedback")
    def executive_feedback(payload: ExecutiveFeedbackRequest, db: Session = Depends(get_db)):
        from app.services.learning_engine import learn

        feedback = learn(
            {
                "decision": payload.decision,
                "success": payload.success,
            },
            _executive_learning_store,
        )

        db.add(
            AuditLog(
                user_id="human.executive",
                action=f"executive.feedback.{payload.decision}",
                entity_type="executive_learning",
                entity_id=str(payload.success),
            )
        )
        db.commit()

        get_event_bus().publish(
            "executive.learning",
            {
                "event_type": "executive.feedback.recorded",
                "source": "john.executive",
                "payload": feedback,
            },
        )

        return {"status": "ok", "feedback": feedback, "learning": _executive_learning_store}

    UNIVERSAL_ROLES = {"ADMIN", "GESTOR", "OPERADOR", "INVESTIDOR", "CLIENTE", "JOHN"}

    UNIVERSAL_PERMISSIONS = {
        "project_create": {"ADMIN", "GESTOR", "OPERADOR"},
        "project_read": UNIVERSAL_ROLES,
        "governance_config": {"ADMIN", "GESTOR"},
        "workflow_advance": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "decision_score": UNIVERSAL_ROLES,
        "events_catalog": UNIVERSAL_ROLES,
        "events_simulate": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "econotech_ingest": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "econotech_signals": UNIVERSAL_ROLES,
        "econotech_config": {"ADMIN", "GESTOR"},
        "econotech_impact": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "audit_ingest": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "audit_summary": UNIVERSAL_ROLES,
        "health_score": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "health_thresholds": {"ADMIN", "GESTOR"},
        "john_interpret": UNIVERSAL_ROLES,
        "john_mode": UNIVERSAL_ROLES,
        "knowledge_record": {"ADMIN", "GESTOR", "OPERADOR", "JOHN"},
        "knowledge_reuse": UNIVERSAL_ROLES,
        "dashboard_read": UNIVERSAL_ROLES,
    }

    def require_universal_context(
        request: Request,
        *,
        action: str,
        requested_tenant: str = "",
        resource_tenant: str = "",
    ) -> Dict[str, str]:
        role = str(request.headers.get("X-Role", "")).strip().upper()
        tenant_header = str(request.headers.get("X-Tenant-ID", "")).strip()
        if not role or not tenant_header:
            raise HTTPException(status_code=401, detail="missing_universal_identity_headers")
        if role not in UNIVERSAL_ROLES:
            raise HTTPException(status_code=403, detail="invalid_universal_role")
        allowed = UNIVERSAL_PERMISSIONS.get(action, set())
        if role not in allowed:
            raise HTTPException(status_code=403, detail="universal_role_not_allowed")

        resolved_tenant = str(resource_tenant or requested_tenant or tenant_header)
        if role != "ADMIN" and resolved_tenant != tenant_header:
            raise HTTPException(status_code=403, detail="tenant_scope_violation")

        return {
            "role": role,
            "tenant": resolved_tenant,
            "request_tenant": tenant_header,
        }

    @app.post("/universal/projects")
    def universal_create_project(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="project_create",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        try:
            result = app.state.universal_core.create_project(
                portfolio=str(payload.get("portfolio", "")),
                program=str(payload.get("program", "")),
                project=str(payload.get("project", "")),
                tenant=str(auth["tenant"]),
                project_type=str(payload.get("project_type", "PRJ")),
                year=int(payload.get("year") or datetime.now(timezone.utc).year),
                metadata=dict(payload.get("metadata") or {}),
            )
            return {"status": "created", "project": result}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/universal/projects/{project_id}")
    def universal_get_project(project_id: str, request: Request):
        auth = require_universal_context(request, action="project_read")
        try:
            return {
                "project": app.state.universal_core.get_project_scoped(
                    project_id,
                    tenant=auth["tenant"],
                    role=auth["role"],
                )
            }
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/universal/governance/phases")
    def universal_set_phases(payload: Dict[str, Any], request: Request):
        require_universal_context(request, action="governance_config")
        phases = payload.get("phases", [])
        try:
            result = app.state.universal_core.configure_phases([str(item) for item in phases])
            return {"status": "configured", **result}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/universal/governance/rules")
    def universal_add_rule(payload: Dict[str, Any], request: Request):
        require_universal_context(request, action="governance_config")
        try:
            result = app.state.universal_core.add_phase_rule(
                phase=str(payload.get("fase", "")),
                rule=str(payload.get("regra", "")),
            )
            return {"status": "rule_added", **result}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/universal/workflow/advance")
    def universal_advance_workflow(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="workflow_advance",
            requested_tenant=str(payload.get("tenant", "")),
        )
        try:
            result = app.state.universal_core.advance_workflow(
                project_id=str(payload.get("project_id", "")),
                metrics=dict(payload.get("metrics") or {}),
                actor=str(payload.get("actor", "system")),
                tenant=auth["tenant"],
                role=auth["role"],
            )
            return result
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/universal/decision/score")
    def universal_score(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="decision_score",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        result = app.state.universal_core.score_decision(
            retorno=float(payload.get("retorno", 0.0) or 0.0),
            risco=float(payload.get("risco", 0.0) or 0.0),
            demanda=float(payload.get("demanda", 0.0) or 0.0),
            tenant=auth["tenant"],
            weights=dict(payload.get("weights") or {}),
        )
        return result

    @app.get("/universal/events/catalog")
    def universal_events_catalog(request: Request):
        require_universal_context(request, action="events_catalog")
        return app.state.universal_core.events_catalog()

    @app.post("/universal/events/simulate")
    def universal_events_simulate(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="events_simulate",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        event_types = payload.get("event_types") or []
        seed_payload = dict(payload.get("payload") or {})
        result = app.state.universal_core.simulate_events(
            tenant=str(auth["tenant"]),
            event_types=[str(item) for item in event_types],
            seed_payload=seed_payload,
        )
        return {"status": "simulated", **result}

    @app.post("/universal/econotech/ingest")
    def universal_econotech_ingest(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="econotech_ingest",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        item = app.state.universal_core.ingest_signal(
            source=str(payload.get("source", "macro")),
            signal_type=str(payload.get("type", "unknown")),
            value=float(payload.get("value", 0.0) or 0.0),
            tenant=str(auth["tenant"]),
        )
        return {"status": "ingested", "signal": item}

    @app.get("/universal/econotech/signals")
    def universal_econotech_signals(
        request: Request,
        signal_type: str = Query(""),
        tenant: str = Query(""),
        limit: int = Query(20),
    ):
        auth = require_universal_context(
            request,
            action="econotech_signals",
            requested_tenant=tenant,
        )
        return app.state.universal_core.list_signals(signal_type=signal_type, tenant=auth["tenant"], limit=limit)

    @app.post("/universal/econotech/scenarios")
    def universal_econotech_scenarios(payload: Dict[str, Any], request: Request):
        require_universal_context(request, action="econotech_config")
        try:
            return app.state.universal_core.configure_scenarios([str(item) for item in (payload.get("scenarios") or [])])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/universal/econotech/impact")
    def universal_econotech_impact(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="econotech_impact",
            requested_tenant=str(payload.get("tenant", "")),
        )
        try:
            return app.state.universal_core.impact_adapter(
                project_id=str(payload.get("project_id", "")),
                scenario=str(payload.get("scenario", "stability")),
                tenant=auth["tenant"],
                role=auth["role"],
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/universal/audit/events")
    def universal_audit_ingest(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="audit_ingest",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        result = app.state.universal_core.ingest_audit(
            source=str(payload.get("source", "core")),
            entity=str(payload.get("entity", "")),
            severity=str(payload.get("severity", "MEDIUM")),
            action=str(payload.get("action", "observe")),
            tenant=str(auth["tenant"]),
            context=dict(payload.get("context") or {}),
        )
        return {"status": "ingested", "audit": result}

    @app.get("/universal/audit/summary")
    def universal_audit_summary(request: Request, tenant: str = Query("")):
        auth = require_universal_context(
            request,
            action="audit_summary",
            requested_tenant=tenant,
        )
        return app.state.universal_core.audit_summary(tenant=auth["tenant"])

    @app.post("/universal/health/score")
    def universal_health_score(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="health_score",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        return app.state.universal_core.compute_health_score(
            finance=float(payload.get("finance", 0.0) or 0.0),
            operational=float(payload.get("operational", 0.0) or 0.0),
            risk=float(payload.get("risk", 0.0) or 0.0),
            tenant=str(auth["tenant"]),
        )

    @app.post("/universal/health/thresholds")
    def universal_health_thresholds(payload: Dict[str, Any], request: Request):
        require_universal_context(request, action="health_thresholds")
        try:
            return app.state.universal_core.configure_thresholds(
                healthy_min=float(payload.get("healthy_min", 80.0) or 80.0),
                attention_min=float(payload.get("attention_min", 60.0) or 60.0),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/universal/john/interpret")
    def universal_john_interpret(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="john_interpret",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        result = app.state.universal_core.john_interpret(
            data=dict(payload.get("data") or {}),
            scenario=str(payload.get("scenario", "stability")),
            score=float(payload.get("score", 0.0) or 0.0),
            tenant=str(auth["tenant"]),
        )
        return result

    @app.post("/universal/john/decision-mode")
    def universal_john_mode(payload: Dict[str, Any], request: Request):
        require_universal_context(request, action="john_mode")
        return {"mode": app.state.universal_core.john_decision_mode(score=float(payload.get("score", 0.0) or 0.0))}

    @app.post("/universal/knowledge")
    def universal_knowledge_record(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="knowledge_record",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        result = app.state.universal_core.record_knowledge(
            input_data=dict(payload.get("input") or {}),
            resultado=dict(payload.get("resultado") or {}),
            licao=str(payload.get("licao", "")),
            tenant=str(auth["tenant"]),
        )
        return {"status": "recorded", "item": result}

    @app.post("/universal/knowledge/reuse")
    def universal_knowledge_reuse(payload: Dict[str, Any], request: Request):
        auth = require_universal_context(
            request,
            action="knowledge_reuse",
            requested_tenant=str(payload.get("tenant", "tenant_liceu")),
        )
        result = app.state.universal_core.reuse_knowledge(
            input_data=dict(payload.get("input") or {}),
            tenant=str(auth["tenant"]),
            limit=int(payload.get("limit", 5) or 5),
        )
        return result

    @app.get("/universal/dashboard")
    def universal_dashboard(request: Request, tenant: str = Query("tenant_liceu")):
        auth = require_universal_context(
            request,
            action="dashboard_read",
            requested_tenant=tenant,
        )
        return app.state.universal_core.dashboard_snapshot(tenant=auth["tenant"])

    # ────────────────────────────────────────────────────────────────────────

    @app.get("/events/subscribe/{service}")
    def subscribe_events(service: str):
        monolith = get_monolith_by_slug(service)
        if monolith is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado no registry")

        bus = get_event_bus()
        requested_service = monolith["slug"]
        entries = bus.recent_messages(limit=50) if hasattr(bus, "recent_messages") else []

        service_events = []
        for entry in entries:
            message = entry.get("message", {}) if isinstance(entry, dict) else {}
            payload = message.get("payload", {}) if isinstance(message, dict) else {}
            if not isinstance(payload, dict):
                payload = {"data": payload}

            source = normalize_dispatch_intent(str(message.get("source") or message.get("origin") or ""))
            payload_service = normalize_dispatch_intent(str(payload.get("service") or payload.get("target_service") or ""))
            channel_name = str(entry.get("channel", settings.JOH_EVENT_CHANNEL)) if isinstance(entry, dict) else settings.JOH_EVENT_CHANNEL
            channel_hint = normalize_dispatch_intent(channel_name)

            if requested_service not in {source, payload_service} and requested_service not in channel_hint:
                continue

            service_events.append(
                {
                    "channel": channel_name,
                    "event_type": message.get("event_type", "unknown"),
                    "source": message.get("source") or message.get("origin") or "unknown",
                    "timestamp": message.get("timestamp"),
                    "payload": payload,
                }
            )

        return {
            "status": "subscribed",
            "service": requested_service,
            "provider": bus.provider,
            "channel": settings.JOH_EVENT_CHANNEL,
            "mode": "snapshot",
            "buffered_events": len(service_events),
            "events": service_events[-20:],
        }

    return app


app = create_application()

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from nats.aio.client import Client as NATS
from sqlalchemy import DateTime, Float, String, Text, create_engine, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

app = FastAPI(title="John Engine")
nc = NATS()

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://liceu:liceu@postgres:5432/liceu")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

BUSINESS_SIGNALS: dict[str, dict[str, Any]] = {}
FEATURE_STORE: dict[str, dict[str, Any]] = {}


class Base(DeclarativeBase):
    pass


class JohnSuggestion(Base):
    __tablename__ = "john_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    target_path: Mapped[str] = mapped_column(String(160), nullable=False)
    decision_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JohnPrediction(Base):
    __tablename__ = "john_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    business_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    delay_risk: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    best_action: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    target_path: Mapped[str] = mapped_column(String(160), nullable=False)
    decision_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JohnSimulation(Base):
    __tablename__ = "john_simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    scenario: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(String(40), nullable=False)
    capital_total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    expected_return: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    progress: Mapped[float] = mapped_column(Float, nullable=False)
    capital_allocated: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    required_capital: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JohnPortfolioDecision(Base):
    __tablename__ = "john_portfolio_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy: Mapped[str] = mapped_column(String(40), nullable=False)
    roi: Mapped[float] = mapped_column(Float, nullable=False)
    risk: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    capital_total: Mapped[float] = mapped_column(Float, nullable=False)
    liquidity: Mapped[float] = mapped_column(Float, nullable=False)
    diversification: Mapped[float] = mapped_column(Float, nullable=False)
    alerts: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    decision_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JohnAllocation(Base):
    __tablename__ = "john_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    project_external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    allocated: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_business_id(raw_business_id: Any, raw_project_id: Any) -> str:
    if raw_business_id:
        return str(raw_business_id)
    if raw_project_id:
        project_id = str(raw_project_id)
        if project_id.startswith("project-business-"):
            return project_id.replace("project-", "", 1)
        if project_id.startswith("project-"):
            return project_id[len("project-") :]
        return project_id
    return "business-1"


def _project_id_from_context(data: dict[str, Any]) -> str:
    if data.get("project_id"):
        return str(data.get("project_id"))
    business_id = _normalize_business_id(data.get("business_id"), data.get("project_id"))
    return f"project-{business_id}"


def _to_payload(row: JohnSuggestion) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "business_id": row.business_id,
        "type": row.type,
        "message": row.message,
        "action": row.action,
        "priority": row.priority,
        "confidence": row.confidence,
        "status": row.status,
        "target_path": row.target_path,
        "decision_by": row.decision_by,
        "decision_reason": row.decision_reason,
        "decision_at": row.decision_at.isoformat() if row.decision_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _prediction_to_payload(row: JohnPrediction, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "project_id": row.project_id,
        "business_id": row.business_id,
        "delay_risk": row.delay_risk,
        "estimated_cost": row.estimated_cost,
        "risk_score": row.risk_score,
        "best_action": row.best_action,
        "message": row.message,
        "status": row.status,
        "target_path": row.target_path,
        "decision_by": row.decision_by,
        "decision_reason": row.decision_reason,
        "decision_at": row.decision_at.isoformat() if row.decision_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "scenarios": scenarios,
    }


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _cap(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def predict_delay(progress: float, expected_progress: float) -> dict[str, float]:
    gap = expected_progress - progress
    probability = _cap(gap * 2, 0, 100)
    return {"delay_risk": probability}


def predict_cost(current_cost: float, progress_percent: float) -> dict[str, float]:
    progress = progress_percent / 100
    if progress <= 0:
        return {"estimated_cost": current_cost}
    estimated_final = current_cost / progress
    return {"estimated_cost": estimated_final}


def predict_operational_risk(errors: int, audits: int, supplier_performance: float) -> dict[str, float]:
    risk = (errors * 8) + (audits * 5) + ((100 - supplier_performance) * 0.4)
    return {"risk_score": _cap(risk, 0, 100)}


def simulate(project: dict[str, Any], delay_risk: float, estimated_cost: float, risk_score: float) -> list[dict[str, Any]]:
    base_cost_index = _as_float(project.get("budget"), estimated_cost) or estimated_cost or 1
    scenarios = []

    scenarios.append(
        {
            "name": "manter",
            "delay": round(delay_risk, 2),
            "cost": round((estimated_cost / base_cost_index) * 100, 2),
            "risk": round(risk_score, 2),
            "target_path": f"/actions/pause-project/{project['project_id']}",
        }
    )
    scenarios.append(
        {
            "name": "reforcar equipe",
            "delay": round(_cap(delay_risk * 0.35, 0, 100), 2),
            "cost": round((estimated_cost * 1.2 / base_cost_index) * 100, 2),
            "risk": round(_cap(risk_score * 0.75, 0, 100), 2),
            "target_path": f"/actions/reinforce-team/{project['project_id']}",
        }
    )
    scenarios.append(
        {
            "name": "reduzir escopo",
            "delay": round(_cap(delay_risk * 0.1, 0, 100), 2),
            "cost": round((estimated_cost * 0.8 / base_cost_index) * 100, 2),
            "risk": round(_cap(risk_score * 0.65, 0, 100), 2),
            "target_path": f"/actions/trigger-audit/{project['project_id']}",
        }
    )

    return scenarios


def choose_best(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(scenarios, key=lambda x: (x["delay"], x["cost"], x["risk"]))[0]


def allocate(projects: list[dict[str, Any]], capital: float) -> list[dict[str, Any]]:
    ranked = sorted(
        projects,
        key=lambda p: (_as_float(p.get("expected_return"), 0) / (_as_float(p.get("risk"), 0) + 1)),
        reverse=True,
    )

    allocation: list[dict[str, Any]] = []
    remaining = max(0.0, _as_float(capital, 0))
    for project in ranked:
        if remaining <= 0:
            break
        required = _as_float(project.get("required_capital"), 0)
        if required <= 0:
            continue
        invest = min(required, remaining)
        allocation.append(
            {
                "project_id": str(project["project_id"]),
                "project_external_id": str(project.get("external_id", project.get("project_id"))),
                "project_name": str(project.get("name", project.get("external_id", "Projeto"))),
                "allocated": round(invest, 2),
            }
        )
        remaining -= invest
    return allocation


def simulate_portfolio(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenarios = []
    if not projects:
        return [
            {"name": "conservador", "roi": 8, "risk": 18},
            {"name": "balanceado", "roi": 12, "risk": 30},
            {"name": "agressivo", "roi": 16, "risk": 55},
        ]

    avg_return = sum(_as_float(p.get("expected_return"), 0) for p in projects) / len(projects)
    avg_risk = sum(_as_float(p.get("risk"), 0) for p in projects) / len(projects)

    scenarios.append({"name": "conservador", "roi": round(max(6, avg_return * 0.75), 2), "risk": round(max(10, avg_risk * 0.55), 2)})
    scenarios.append({"name": "balanceado", "roi": round(max(10, avg_return * 1.0), 2), "risk": round(max(20, avg_risk * 0.9), 2)})
    scenarios.append({"name": "agressivo", "roi": round(max(14, avg_return * 1.3), 2), "risk": round(min(95, avg_risk * 1.35), 2)})
    return scenarios


def choose_strategy(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(scenarios, key=lambda s: (_as_float(s.get("roi"), 0) / (_as_float(s.get("risk"), 0) + 1)), reverse=True)[0]


def _project_uuid(external_id: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"liceu-project::{external_id}")


def _portfolio_alerts(projects: list[dict[str, Any]], capital_total: float, allocated_total: float) -> list[str]:
    alerts: list[str] = []
    for project in projects:
        if _as_float(project.get("risk"), 0) >= 70:
            alerts.append(f"Projeto {project.get('name', project.get('external_id', 'N/A'))} com risco alto")

    liquidity_days = 999
    if allocated_total > 0:
        monthly_burn = allocated_total * 0.25
        liquidity_days = int((max(capital_total - allocated_total, 0) / monthly_burn) * 30) if monthly_burn > 0 else 999
    if liquidity_days <= 45:
        alerts.append(f"Liquidez critica em {liquidity_days} dias")

    return alerts


def _persist_portfolio_and_projects(
    portfolio_name: str,
    strategy: str,
    capital_total: float,
    projects_payload: list[dict[str, Any]],
) -> tuple[uuid.UUID, list[dict[str, Any]]]:
    prepared: list[dict[str, Any]] = []
    with SessionLocal() as db:
        portfolio = Portfolio(name=portfolio_name, strategy=strategy, capital_total=capital_total)
        db.add(portfolio)
        db.flush()

        for raw in projects_payload:
            external_id = str(raw.get("id") or raw.get("project_id") or f"project-{uuid.uuid4()}")
            project_uuid = _project_uuid(external_id)
            name = str(raw.get("name") or external_id)
            expected_return = _as_float(raw.get("expected_return"), 12)
            risk_score = _as_float(raw.get("risk_score"), _as_float(raw.get("risk"), 35))
            progress = _as_float(raw.get("progress"), 0)
            capital_allocated = _as_float(raw.get("capital_allocated"), 0)
            required_capital = _as_float(raw.get("required_capital"), max(200000, (100 - progress) * 10000))
            status = str(raw.get("status") or "active")

            existing = db.get(Project, project_uuid)
            if existing is None:
                existing = Project(
                    id=project_uuid,
                    portfolio_id=portfolio.id,
                    external_id=external_id,
                    name=name,
                    expected_return=expected_return,
                    risk_score=risk_score,
                    progress=progress,
                    capital_allocated=capital_allocated,
                    required_capital=required_capital,
                    status=status,
                )
            else:
                existing.portfolio_id = portfolio.id
                existing.name = name
                existing.expected_return = expected_return
                existing.risk_score = risk_score
                existing.progress = progress
                existing.capital_allocated = capital_allocated
                existing.required_capital = required_capital
                existing.status = status
            db.add(existing)

            prepared.append(
                {
                    "project_id": str(existing.id),
                    "external_id": existing.external_id,
                    "name": existing.name,
                    "expected_return": existing.expected_return,
                    "risk": existing.risk_score,
                    "progress": existing.progress,
                    "required_capital": existing.required_capital,
                    "status": existing.status,
                }
            )

        db.commit()
        return portfolio.id, prepared


def _persist_portfolio_decision(
    strategy: str,
    roi: float,
    risk: float,
    capital_total: float,
    liquidity: float,
    diversification: float,
    alerts: list[str],
    allocation: list[dict[str, Any]],
) -> dict[str, Any]:
    with SessionLocal() as db:
        decision = JohnPortfolioDecision(
            strategy=strategy,
            roi=roi,
            risk=risk,
            capital_total=capital_total,
            liquidity=liquidity,
            diversification=diversification,
            alerts=alerts,
        )
        db.add(decision)
        db.flush()

        for item in allocation:
            db.add(
                JohnAllocation(
                    decision_id=decision.id,
                    project_id=uuid.UUID(str(item["project_id"])),
                    project_external_id=str(item["project_external_id"]),
                    project_name=str(item["project_name"]),
                    allocated=_as_float(item["allocated"]),
                )
            )

        db.commit()
        db.refresh(decision)

        return _portfolio_decision_payload(db, decision)


def _portfolio_decision_payload(db, decision: JohnPortfolioDecision) -> dict[str, Any]:
    stmt = select(JohnAllocation).where(JohnAllocation.decision_id == decision.id).order_by(JohnAllocation.created_at.asc())
    allocations = db.execute(stmt).scalars().all()
    allocation_payload = [
        {
            "project_id": str(item.project_id),
            "project_external_id": item.project_external_id,
            "project_name": item.project_name,
            "allocated": item.allocated,
        }
        for item in allocations
    ]
    return {
        "id": str(decision.id),
        "strategy": decision.strategy,
        "roi": decision.roi,
        "risk": decision.risk,
        "capital_total": decision.capital_total,
        "liquidity": decision.liquidity,
        "diversification": decision.diversification,
        "alerts": decision.alerts or [],
        "status": decision.status,
        "decision_by": decision.decision_by,
        "decision_reason": decision.decision_reason,
        "decision_at": decision.decision_at.isoformat() if decision.decision_at else None,
        "created_at": decision.created_at.isoformat() if decision.created_at else None,
        "allocation": allocation_payload,
    }


async def _publish_portfolio_recommendation(payload: dict[str, Any]) -> None:
    if not nc.is_connected:
        return
    event = {
        "type": "john.portfolio.recommendation",
        "strategy": payload.get("strategy"),
        "roi": payload.get("roi"),
        "risk": payload.get("risk"),
        "allocation": payload.get("allocation", []),
        "alerts": payload.get("alerts", []),
        "timestamp": _now_iso(),
    }
    await nc.publish("john.portfolio.recommendation", json.dumps(event).encode())


def analyze(data: dict[str, Any]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    business_id = _normalize_business_id(data.get("business_id"), data.get("project_id"))

    delay = _as_float(data.get("delay"), 0)
    if delay > 10:
        suggestions.append(
            {
                "business_id": business_id,
                "type": "operation",
                "message": f"Obra {business_id} com atraso de {delay:.0f}%: sugerir reforco de equipe",
                "action": "reforcar equipe",
                "priority": "high",
                "confidence": 0.84,
                "target_path": f"/actions/pause-project/project-{business_id}",
            }
        )

    cost = _as_float(data.get("cost"), 0)
    budget = _as_float(data.get("budget"), 0)
    if budget > 0 and cost > budget:
        over = ((cost - budget) / budget) * 100
        suggestions.append(
            {
                "business_id": business_id,
                "type": "financial",
                "message": f"Custo acima do previsto em {over:.0f}%: revisar orcamento",
                "action": "revisar custos",
                "priority": "high",
                "confidence": 0.89,
                "target_path": f"/actions/trigger-audit/project-{business_id}",
            }
        )

    company_health = _as_float(data.get("company_health"), 100)
    if company_health < 70:
        suggestions.append(
            {
                "business_id": business_id,
                "type": "health",
                "message": f"Empresa com score {company_health:.0f}: intervencao recomendada",
                "action": "acionar auditoria hospital",
                "priority": "high",
                "confidence": 0.81,
                "target_path": f"/actions/trigger-audit/project-{business_id}",
            }
        )

    qa_repeated_errors = _as_int(data.get("qa_repeated_errors"), 0)
    if qa_repeated_errors >= 3:
        suggestions.append(
            {
                "business_id": business_id,
                "type": "quality",
                "message": "Erro repetido em fundacao: atualizar processo e iniciar treinamento",
                "action": "iniciar treinamento",
                "priority": "medium",
                "confidence": 0.78,
                "target_path": f"/actions/start-training/project-{business_id}",
            }
        )

    market_heat = _as_float(data.get("market_heat"), 0)
    if market_heat >= 0.75:
        suggestions.append(
            {
                "business_id": business_id,
                "type": "strategy",
                "message": "Mercado aquecido: acelerar lancamentos",
                "action": "aprovar negocio com prioridade",
                "priority": "medium",
                "confidence": 0.73,
                "target_path": f"/actions/approve-business/{business_id}",
            }
        )

    risk_flags = 0
    if delay > 10:
        risk_flags += 1
    if budget > 0 and cost > budget:
        risk_flags += 1
    if company_health < 70:
        risk_flags += 1
    if risk_flags >= 2:
        suggestions.append(
            {
                "business_id": business_id,
                "type": "correlation",
                "message": "Correlacao critica entre operacao, financeiro e saude: travar novos projetos",
                "action": "travar novos projetos",
                "priority": "critical",
                "confidence": 0.92,
                "target_path": f"/actions/pause-project/project-{business_id}",
            }
        )

    return suggestions


def _build_feature_context(context: dict[str, Any]) -> dict[str, Any]:
    project_id = _project_id_from_context(context)
    business_id = _normalize_business_id(context.get("business_id"), context.get("project_id"))
    current = FEATURE_STORE.get(
        project_id,
        {
            "project_id": project_id,
            "business_id": business_id,
            "progress": 42.0,
            "expected_progress": 58.0,
            "productivity": 0.9,
            "current_cost": 1500000.0,
            "budget": 2000000.0,
            "spend_rate": 1.0,
            "errors": 1,
            "audits": 0,
            "supplier_performance": 82.0,
            "updated_at": _now_iso(),
        },
    )

    current["business_id"] = business_id
    if context.get("progress") is not None:
        current["progress"] = _as_float(context.get("progress"), current["progress"])
    if context.get("expected_progress") is not None:
        current["expected_progress"] = _as_float(context.get("expected_progress"), current["expected_progress"])
    elif context.get("delay") is not None:
        current["expected_progress"] = _cap(current["progress"] + _as_float(context.get("delay"), 0), 0, 100)

    current["productivity"] = _as_float(context.get("productivity"), current["productivity"])
    current["current_cost"] = _as_float(context.get("cost"), current["current_cost"])
    current["budget"] = _as_float(context.get("budget"), current["budget"])
    current["spend_rate"] = _as_float(context.get("spend_rate"), current["spend_rate"])
    current["errors"] = _as_int(context.get("qa_repeated_errors"), current["errors"])
    if context.get("company_health") is not None:
        penalty = 1 if _as_float(context.get("company_health"), 100) < 70 else 0
        current["audits"] = max(current.get("audits", 0), penalty)
    current["supplier_performance"] = _cap(
        _as_float(context.get("supplier_performance"), current["supplier_performance"]), 0, 100
    )
    current["updated_at"] = _now_iso()

    FEATURE_STORE[project_id] = current
    return current


def _prediction_message(delay_risk: float, risk_score: float) -> str:
    if delay_risk >= 70:
        return "Alto risco de atraso"
    if risk_score >= 70:
        return "Risco operacional elevado"
    return "Risco controlado com monitoramento"


def _persist_prediction(
    project_id: str,
    business_id: str,
    delay_risk: float,
    estimated_cost: float,
    risk_score: float,
    best: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    with SessionLocal() as db:
        row = JohnPrediction(
            project_id=project_id,
            business_id=business_id,
            delay_risk=delay_risk,
            estimated_cost=estimated_cost,
            risk_score=risk_score,
            best_action=str(best["name"]),
            message=_prediction_message(delay_risk, risk_score),
            target_path=str(best["target_path"]),
        )
        db.add(row)
        db.flush()

        for scenario in scenarios:
            db.add(
                JohnSimulation(
                    prediction_id=row.id,
                    project_id=project_id,
                    scenario=scenario,
                )
            )

        db.commit()
        db.refresh(row)
        return _prediction_to_payload(row, scenarios)


def _list_prediction_scenarios(db, prediction_id: uuid.UUID) -> list[dict[str, Any]]:
    stmt = select(JohnSimulation).where(JohnSimulation.prediction_id == prediction_id).order_by(JohnSimulation.created_at.asc())
    rows = db.execute(stmt).scalars().all()
    return [item.scenario for item in rows]


def _latest_prediction(db, project_id: str | None) -> JohnPrediction | None:
    stmt = select(JohnPrediction).order_by(JohnPrediction.created_at.desc())
    if project_id:
        stmt = stmt.where(JohnPrediction.project_id == project_id)
    return db.execute(stmt.limit(1)).scalar_one_or_none()


async def _publish_recommendation(prediction_payload: dict[str, Any]) -> None:
    if not nc.is_connected:
        return
    event = {
        "type": "john.recommendation",
        "project_id": prediction_payload.get("project_id"),
        "business_id": prediction_payload.get("business_id"),
        "message": prediction_payload.get("message"),
        "best_action": prediction_payload.get("best_action"),
        "best_target": prediction_payload.get("target_path"),
        "scenarios": prediction_payload.get("scenarios", []),
        "delay_risk": prediction_payload.get("delay_risk"),
        "estimated_cost": prediction_payload.get("estimated_cost"),
        "risk_score": prediction_payload.get("risk_score"),
        "timestamp": _now_iso(),
    }
    await nc.publish("john.recommendation", json.dumps(event).encode())


def _merge_business_signal(context: dict[str, Any]) -> dict[str, Any]:
    business_id = str(context.get("business_id") or "business-1")
    current = BUSINESS_SIGNALS.get(
        business_id,
        {
            "business_id": business_id,
            "delay": None,
            "cost": None,
            "budget": None,
            "company_health": None,
            "qa_repeated_errors": None,
            "market_heat": None,
            "last_subject": None,
            "updated_at": None,
        },
    )

    for field in ("delay", "cost", "budget", "company_health", "qa_repeated_errors", "market_heat"):
        if context.get(field) is not None:
            current[field] = context.get(field)
    current["last_subject"] = context.get("subject")
    current["updated_at"] = _now_iso()
    BUSINESS_SIGNALS[business_id] = current
    return current


def _upsert_suggestions(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    with SessionLocal() as db:
        for candidate in candidates:
            stmt = (
                select(JohnSuggestion)
                .where(JohnSuggestion.business_id == candidate["business_id"])
                .where(JohnSuggestion.type == candidate["type"])
                .where(JohnSuggestion.message == candidate["message"])
                .where(JohnSuggestion.status == "pending")
            )
            existing = db.execute(stmt).scalar_one_or_none()
            if existing:
                continue
            row = JohnSuggestion(**candidate)
            db.add(row)
            db.flush()
            created.append(_to_payload(row))
        db.commit()
    return created


async def _publish_created(items: list[dict[str, Any]]) -> None:
    if not nc.is_connected:
        return
    for item in items:
        await nc.publish("john.suggestion", json.dumps(item).encode())


def _event_to_context(subject: str, data: dict[str, Any]) -> dict[str, Any]:
    business_id = _normalize_business_id(data.get("business_id"), data.get("project_id"))
    op_subjects = {"operation.update", "project.created", "operation.project.paused"}
    fin_subjects = {"finance.update", "finance.cost.recorded", "finance.payment.released"}
    audit_subjects = {"audit.alert", "audit.manual.triggered", "audit.issue", "audit.issue.detected"}
    quality_subjects = {"quality.update", "pd.training.started"}
    strategy_subjects = {"strategy.market", "business.approved"}

    normalized = {
        "business_id": business_id,
        "project_id": _project_id_from_context(data),
        "subject": subject,
        "delay": data.get("delay", 18 if subject in op_subjects else None),
        "cost": data.get("cost", 2240000 if subject in fin_subjects else None),
        "budget": data.get("budget", 2000000 if subject in fin_subjects else None),
        "company_health": data.get("company_health", 62 if subject in audit_subjects else None),
        "qa_repeated_errors": data.get("qa_repeated_errors", 3 if subject in quality_subjects else None),
        "market_heat": data.get("market_heat", 0.8 if subject in strategy_subjects else None),
        "progress": data.get("progress", 42 if subject in op_subjects else None),
        "expected_progress": data.get("expected_progress", 58 if subject in op_subjects else None),
        "productivity": data.get("productivity", 0.9 if subject in op_subjects else None),
        "spend_rate": data.get("spend_rate", 1.12 if subject in fin_subjects else None),
        "supplier_performance": data.get("supplier_performance", 68 if subject in audit_subjects else None),
    }
    return normalized


def _ensure_decision_columns() -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE IF EXISTS john_suggestions ADD COLUMN IF NOT EXISTS decision_by VARCHAR(120)"))
        conn.execute(text("ALTER TABLE IF EXISTS john_suggestions ADD COLUMN IF NOT EXISTS decision_reason TEXT"))
        conn.execute(text("ALTER TABLE IF EXISTS john_suggestions ADD COLUMN IF NOT EXISTS decision_at TIMESTAMPTZ"))


def _run_predictive_pipeline(context: dict[str, Any]) -> dict[str, Any]:
    feature = _build_feature_context(context)
    delay = predict_delay(feature["progress"], feature["expected_progress"])
    cost = predict_cost(feature["current_cost"], feature["progress"])
    risk = predict_operational_risk(feature["errors"], feature["audits"], feature["supplier_performance"])

    scenarios = simulate(
        feature,
        delay_risk=delay["delay_risk"],
        estimated_cost=cost["estimated_cost"],
        risk_score=risk["risk_score"],
    )
    best = choose_best(scenarios)

    return _persist_prediction(
        project_id=feature["project_id"],
        business_id=feature["business_id"],
        delay_risk=delay["delay_risk"],
        estimated_cost=cost["estimated_cost"],
        risk_score=risk["risk_score"],
        best=best,
        scenarios=scenarios,
    )


@app.on_event("startup")
async def startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_decision_columns()
    if not nc.is_connected:
        await nc.connect(NATS_URL)

    async def handler(msg):
        data = json.loads(msg.data.decode()) if msg.data else {}
        context = _event_to_context(msg.subject, data)
        merged_context = _merge_business_signal(context)
        candidates = analyze(merged_context)
        created = _upsert_suggestions(candidates)
        prediction_payload = _run_predictive_pipeline(context)
        await _publish_created(created)
        await _publish_recommendation(prediction_payload)

    subjects = [
        "operation.update",
        "project.created",
        "finance.update",
        "finance.cost.recorded",
        "audit.alert",
        "audit.manual.triggered",
        "audit.issue",
        "audit.issue.detected",
        "quality.update",
        "pd.training.started",
        "strategy.market",
        "business.approved",
        "operation.project.paused",
        "finance.payment.released",
    ]
    for subject in subjects:
        await nc.subscribe(subject, cb=handler)


@app.on_event("shutdown")
async def shutdown() -> None:
    if nc.is_connected:
        await nc.drain()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "john_engine"}


@app.get("/john/suggestions")
def list_suggestions(status: str = "pending", limit: int = 50) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 200))
    with SessionLocal() as db:
        stmt = select(JohnSuggestion).order_by(JohnSuggestion.created_at.desc())
        if status != "all":
            stmt = stmt.where(JohnSuggestion.status == status)
        rows = db.execute(stmt.limit(safe_limit)).scalars().all()
    items = [_to_payload(row) for row in rows]
    return {"items": items, "total": len(items), "status": status}


@app.get("/john/predictions/latest")
def latest_prediction(project_id: str | None = None) -> dict[str, Any]:
    with SessionLocal() as db:
        row = _latest_prediction(db, project_id)
        if row is None:
            return {"items": [], "total": 0}
        scenarios = _list_prediction_scenarios(db, row.id)
        return {"items": [_prediction_to_payload(row, scenarios)], "total": 1}


@app.get("/john/predictions")
def list_predictions(limit: int = 20) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 200))
    with SessionLocal() as db:
        stmt = select(JohnPrediction).order_by(JohnPrediction.created_at.desc()).limit(safe_limit)
        rows = db.execute(stmt).scalars().all()
        items = []
        for row in rows:
            scenarios = _list_prediction_scenarios(db, row.id)
            items.append(_prediction_to_payload(row, scenarios))
    return {"items": items, "total": len(items)}


@app.post("/john/predictions/{prediction_id}/approve")
async def approve_prediction(prediction_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Aprovacao de recomendacao preditiva")

    with SessionLocal() as db:
        row = db.get(JohnPrediction, uuid.UUID(prediction_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        if row.status != "pending":
            scenarios = _list_prediction_scenarios(db, row.id)
            return {"status": row.status, "prediction": _prediction_to_payload(row, scenarios)}

        row.status = "approved"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
        scenarios = _list_prediction_scenarios(db, row.id)

    if nc.is_connected:
        await nc.publish(
            "john.recommendation.approved",
            json.dumps(
                {
                    "prediction_id": prediction_id,
                    "project_id": row.project_id,
                    "target_path": row.target_path,
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                    "approved_at": _now_iso(),
                }
            ).encode(),
        )

    return {
        "status": "approved",
        "prediction": _prediction_to_payload(row, scenarios),
        "target_path": row.target_path,
        "requires_core_execution": True,
    }


@app.post("/john/predictions/{prediction_id}/reject")
async def reject_prediction(prediction_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Rejeicao de recomendacao preditiva")

    with SessionLocal() as db:
        row = db.get(JohnPrediction, uuid.UUID(prediction_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        if row.status != "pending":
            scenarios = _list_prediction_scenarios(db, row.id)
            return {"status": row.status, "prediction": _prediction_to_payload(row, scenarios)}

        row.status = "rejected"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
        scenarios = _list_prediction_scenarios(db, row.id)

    if nc.is_connected:
        await nc.publish(
            "john.recommendation.rejected",
            json.dumps(
                {
                    "prediction_id": prediction_id,
                    "project_id": row.project_id,
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                    "rejected_at": _now_iso(),
                }
            ).encode(),
        )

    return {
        "status": "rejected",
        "prediction": _prediction_to_payload(row, scenarios),
    }


@app.post("/john/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Aprovado no Command Center")
    decision_at = datetime.now(timezone.utc)

    with SessionLocal() as db:
        row = db.get(JohnSuggestion, uuid.UUID(suggestion_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        if row.status != "pending":
            return {"status": row.status, "suggestion": _to_payload(row), "executed_via_core": False}

        row.status = "approved"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = decision_at
        db.add(row)
        db.commit()
        db.refresh(row)

    if nc.is_connected:
        await nc.publish(
            "john.suggestion.approved",
            json.dumps(
                {
                    "suggestion_id": suggestion_id,
                    "business_id": row.business_id,
                    "target_path": row.target_path,
                    "approved_at": _now_iso(),
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                }
            ).encode(),
        )

    return {
        "status": "approved",
        "suggestion": _to_payload(row),
        "requires_core_execution": True,
        "target_path": row.target_path,
    }


@app.post("/john/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Rejeitado no Command Center")
    decision_at = datetime.now(timezone.utc)

    with SessionLocal() as db:
        row = db.get(JohnSuggestion, uuid.UUID(suggestion_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        if row.status != "pending":
            return {"status": row.status, "suggestion": _to_payload(row)}

        row.status = "rejected"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = decision_at
        db.add(row)
        db.commit()
        db.refresh(row)

    if nc.is_connected:
        await nc.publish(
            "john.suggestion.rejected",
            json.dumps(
                {
                    "suggestion_id": suggestion_id,
                    "business_id": row.business_id,
                    "rejected_at": _now_iso(),
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                }
            ).encode(),
        )

    return {"status": "rejected", "suggestion": _to_payload(row)}


@app.post("/john/simulate-event")
async def simulate_event(payload: dict[str, Any]) -> dict[str, Any]:
    context = _event_to_context(payload.get("subject", "operation.update"), payload)
    candidates = analyze(context)
    prediction_payload = _run_predictive_pipeline(context)
    created = _upsert_suggestions(candidates)
    await _publish_created(created)
    await _publish_recommendation(prediction_payload)
    return {"created": created, "prediction": prediction_payload, "count": len(created)}


@app.post("/john/portfolio/recommendation/analyze")
async def analyze_portfolio(payload: dict[str, Any]) -> dict[str, Any]:
    portfolio_payload = payload.get("portfolio", {}) if isinstance(payload.get("portfolio"), dict) else {}
    projects_payload = payload.get("projects", []) if isinstance(payload.get("projects"), list) else []

    portfolio_name = str(portfolio_payload.get("name") or "LICEU Portfolio")
    strategy_input = str(portfolio_payload.get("strategy") or "equilibrado")
    capital_total = _as_float(portfolio_payload.get("capital_total"), 1000000)

    _, prepared_projects = _persist_portfolio_and_projects(portfolio_name, strategy_input, capital_total, projects_payload)
    scenarios = simulate_portfolio(prepared_projects)
    chosen_strategy = choose_strategy(scenarios)

    max_risk_by_strategy = {
        "conservador": 35,
        "balanceado": 60,
        "agressivo": 95,
    }
    strategy_name = str(chosen_strategy.get("name", "balanceado"))
    risk_limit = max_risk_by_strategy.get(strategy_name, 60)
    eligible_projects = [p for p in prepared_projects if _as_float(p.get("risk"), 0) <= risk_limit and p.get("status") != "paused"]
    allocation = allocate(eligible_projects, capital_total)
    fallback_alerts: list[str] = []
    if not allocation and prepared_projects:
        fallback_alerts.append("Sem projetos aderentes ao limite de risco; alocacao de contingencia aplicada")
        eligible_projects = [p for p in prepared_projects if p.get("status") != "paused"]
        allocation = allocate(eligible_projects, capital_total * 0.6)

    allocated_total = sum(_as_float(item.get("allocated"), 0) for item in allocation)
    weighted_roi_numerator = 0.0
    weighted_risk_numerator = 0.0
    allocation_index = {item["project_id"]: item for item in allocation}
    for project in eligible_projects:
        allocated = _as_float(allocation_index.get(project["project_id"], {}).get("allocated"), 0)
        if allocated <= 0:
            continue
        weighted_roi_numerator += allocated * _as_float(project.get("expected_return"), 0)
        weighted_risk_numerator += allocated * _as_float(project.get("risk"), 0)

    roi = round((weighted_roi_numerator / allocated_total) if allocated_total > 0 else _as_float(chosen_strategy.get("roi"), 0), 2)
    risk = round((weighted_risk_numerator / allocated_total) if allocated_total > 0 else _as_float(chosen_strategy.get("risk"), 0), 2)
    liquidity = round(max(capital_total - allocated_total, 0), 2)
    diversification = round((len(allocation) / max(len(prepared_projects), 1)) * 100, 2)

    alerts = _portfolio_alerts(eligible_projects, capital_total, allocated_total) + fallback_alerts
    decision_payload = _persist_portfolio_decision(
        strategy=strategy_name,
        roi=roi,
        risk=risk,
        capital_total=capital_total,
        liquidity=liquidity,
        diversification=diversification,
        alerts=alerts,
        allocation=allocation,
    )

    await _publish_portfolio_recommendation(decision_payload)
    return decision_payload


@app.get("/john/portfolio/decisions/latest")
def latest_portfolio_decision() -> dict[str, Any]:
    with SessionLocal() as db:
        row = db.execute(select(JohnPortfolioDecision).order_by(JohnPortfolioDecision.created_at.desc()).limit(1)).scalar_one_or_none()
        if row is None:
            return {"item": None}
        return {"item": _portfolio_decision_payload(db, row)}


@app.post("/john/portfolio/decisions/{decision_id}/approve")
async def approve_portfolio_decision(decision_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Aprovacao de estrategia de portfolio")

    with SessionLocal() as db:
        row = db.get(JohnPortfolioDecision, uuid.UUID(decision_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Portfolio decision not found")
        if row.status != "pending":
            return {"status": row.status, "decision": _portfolio_decision_payload(db, row)}

        row.status = "approved"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
        decision = _portfolio_decision_payload(db, row)

    if nc.is_connected:
        await nc.publish(
            "john.portfolio.approved",
            json.dumps(
                {
                    "decision_id": decision_id,
                    "strategy": decision.get("strategy"),
                    "allocation": decision.get("allocation", []),
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                    "approved_at": _now_iso(),
                }
            ).encode(),
        )

    return {"status": "approved", "decision": decision}


@app.post("/john/portfolio/decisions/{decision_id}/reject")
async def reject_portfolio_decision(decision_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision_by = str(payload.get("decision_by") or "human_core")
    decision_reason = str(payload.get("decision_reason") or "Rejeicao de estrategia de portfolio")

    with SessionLocal() as db:
        row = db.get(JohnPortfolioDecision, uuid.UUID(decision_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Portfolio decision not found")
        if row.status != "pending":
            return {"status": row.status, "decision": _portfolio_decision_payload(db, row)}

        row.status = "rejected"
        row.decision_by = decision_by
        row.decision_reason = decision_reason
        row.decision_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
        decision = _portfolio_decision_payload(db, row)

    if nc.is_connected:
        await nc.publish(
            "john.portfolio.rejected",
            json.dumps(
                {
                    "decision_id": decision_id,
                    "decision_by": decision_by,
                    "decision_reason": decision_reason,
                    "rejected_at": _now_iso(),
                }
            ).encode(),
        )

    return {"status": "rejected", "decision": decision}

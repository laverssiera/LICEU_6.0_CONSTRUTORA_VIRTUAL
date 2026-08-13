from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.immutable_audit_service import ImmutableAuditService
from app.models.orchestration import HealthScore, RecoveryPlan


OPEN_STATUSES = {"in_progress", "aggravated"}
ALLOWED_STATUSES = {"in_progress", "completed", "aggravated"}


class RecoveryPlanService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def evaluate_from_health_score(
        self,
        score: HealthScore,
        *,
        threshold_score: int = 60,
        owner: str = "governance_ops",
    ) -> RecoveryPlan | None:
        latest = self._latest_plan(score.company_id)
        open_plan = latest if latest and latest.status in OPEN_STATUSES else None

        if score.score <= threshold_score:
            if open_plan is None:
                plan = RecoveryPlan(
                    company_id=score.company_id,
                    status="in_progress",
                    owner=owner,
                    due_at=datetime.now(timezone.utc) + timedelta(days=30),
                    threshold_score=threshold_score,
                    initial_score=score.score,
                    current_score=score.score,
                    risk_at_creation=score.risk,
                    actions=self._default_actions_for_risk(score.risk),
                    context={
                        "score_history": [
                            {"score": score.score, "risk": score.risk, "at": score.calculated_at.isoformat() if score.calculated_at else None}
                        ]
                    },
                )
                self.db.add(plan)
                self.db.flush()
                ImmutableAuditService(self.db).append(
                    entity_type="recovery_plan",
                    entity_id=plan.id,
                    action="recovery.plan.created",
                    actor="hospital_engine",
                    payload={
                        "company_id": plan.company_id,
                        "initial_score": plan.initial_score,
                        "threshold_score": plan.threshold_score,
                        "status": plan.status,
                    },
                )
                return plan

            self._append_score_history(open_plan, score)
            previous_score = open_plan.current_score
            open_plan.current_score = score.score
            if score.score < previous_score:
                open_plan.status = "aggravated"
            elif score.score >= threshold_score + 10:
                open_plan.status = "completed"
                open_plan.closed_at = datetime.now(timezone.utc)
            ImmutableAuditService(self.db).append(
                entity_type="recovery_plan",
                entity_id=open_plan.id,
                action=f"recovery.plan.updated.{open_plan.status}",
                actor="hospital_engine",
                payload={
                    "company_id": open_plan.company_id,
                    "previous_score": previous_score,
                    "current_score": open_plan.current_score,
                },
            )
            return open_plan

        if open_plan is not None:
            self._append_score_history(open_plan, score)
            open_plan.current_score = score.score
            open_plan.status = "completed"
            open_plan.closed_at = datetime.now(timezone.utc)
            ImmutableAuditService(self.db).append(
                entity_type="recovery_plan",
                entity_id=open_plan.id,
                action="recovery.plan.updated.completed",
                actor="hospital_engine",
                payload={
                    "company_id": open_plan.company_id,
                    "current_score": open_plan.current_score,
                },
            )
            return open_plan

        return None

    def list_plans(
        self,
        *,
        limit: int = 100,
        status: str | None = None,
        company_id: str | None = None,
    ) -> list[RecoveryPlan]:
        query = self.db.query(RecoveryPlan)
        if status:
            query = query.filter(RecoveryPlan.status == status.strip().lower())
        if company_id:
            query = query.filter(RecoveryPlan.company_id == company_id.strip())
        return query.order_by(RecoveryPlan.created_at.desc()).limit(limit).all()

    def update_status(self, plan_id: str, *, status: str, note: str | None = None) -> RecoveryPlan | None:
        normalized_status = status.strip().lower()
        if normalized_status not in ALLOWED_STATUSES:
            raise ValueError("status invalido")

        plan = self.db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
        if plan is None:
            return None

        plan.status = normalized_status
        if normalized_status == "completed":
            plan.closed_at = datetime.now(timezone.utc)

        if note:
            context = dict(plan.context or {})
            notes = list(context.get("notes") or [])
            notes.append({"note": note, "at": datetime.now(timezone.utc).isoformat()})
            context["notes"] = notes
            plan.context = context

        self.db.flush()
        ImmutableAuditService(self.db).append(
            entity_type="recovery_plan",
            entity_id=plan.id,
            action=f"recovery.plan.status.{normalized_status}",
            actor="hospital_ops",
            payload={
                "company_id": plan.company_id,
                "note": note,
            },
        )
        return plan

    def _latest_plan(self, company_id: str) -> RecoveryPlan | None:
        return (
            self.db.query(RecoveryPlan)
            .filter(RecoveryPlan.company_id == company_id)
            .order_by(RecoveryPlan.created_at.desc())
            .first()
        )

    def _append_score_history(self, plan: RecoveryPlan, score: HealthScore) -> None:
        context = dict(plan.context or {})
        history = list(context.get("score_history") or [])
        history.append({"score": score.score, "risk": score.risk, "at": score.calculated_at.isoformat() if score.calculated_at else None})
        context["score_history"] = history[-20:]
        plan.context = context

    def _default_actions_for_risk(self, risk: str) -> list[dict[str, Any]]:
        base_actions = [
            {"type": "task", "owner": "ops_director", "title": "Plano de correcao operacional", "mandatory": True},
            {"type": "training", "owner": "academia_saber", "title": "Treinamento obrigatorio", "mandatory": True},
            {"type": "process_update", "owner": "pdi_ia", "title": "Ajuste de processo", "mandatory": True},
        ]
        if risk in {"high", "critical"}:
            base_actions.append(
                {"type": "financial_review", "owner": "hubbackoffice", "title": "Revisao financeira assistida", "mandatory": True}
            )
        return base_actions


def serialize_recovery_plan(plan: RecoveryPlan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "company_id": plan.company_id,
        "status": plan.status,
        "owner": plan.owner,
        "due_at": plan.due_at.isoformat() if plan.due_at else None,
        "threshold_score": plan.threshold_score,
        "initial_score": plan.initial_score,
        "current_score": plan.current_score,
        "risk_at_creation": plan.risk_at_creation,
        "actions": plan.actions or [],
        "context": plan.context or {},
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        "closed_at": plan.closed_at.isoformat() if plan.closed_at else None,
    }

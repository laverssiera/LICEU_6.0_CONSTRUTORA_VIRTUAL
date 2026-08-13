from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.immutable_audit_service import ImmutableAuditService
from app.models.orchestration import AuditLog, HealthScore, InvestmentEligibilityDecision, RecoveryPlan

OPEN_PLAN_STATUSES = {"in_progress", "aggravated"}
DECISIONS = {"eligible", "monitoring", "restricted"}


class InvestmentEligibilityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def evaluate_company(self, company_id: str, *, actor: str = "system") -> InvestmentEligibilityDecision:
        normalized_company_id = company_id.strip()
        if not normalized_company_id:
            raise ValueError("company_id vazio")

        health_score = self._latest_health_score(normalized_company_id)
        if health_score is None:
            raise ValueError("health_score nao encontrado")

        recovery_plan = self._latest_recovery_plan(normalized_company_id)
        decision, rationale = self._resolve_decision(health_score, recovery_plan)

        item = InvestmentEligibilityDecision(
            company_id=normalized_company_id,
            decision=decision,
            rationale=rationale,
            health_score_id=health_score.id,
            recovery_plan_id=recovery_plan.id if recovery_plan else None,
            context={
                "score": health_score.score,
                "risk": health_score.risk,
                "health_calculated_at": health_score.calculated_at.isoformat() if health_score.calculated_at else None,
                "recovery_plan_status": recovery_plan.status if recovery_plan else None,
                "recovery_plan_current_score": recovery_plan.current_score if recovery_plan else None,
            },
            decided_by=actor,
        )
        self.db.add(item)
        self.db.flush()

        self.db.add(
            AuditLog(
                user_id=None,
                action=f"investment.eligibility.{decision}",
                entity_type="investment_eligibility",
                entity_id=item.id,
            )
        )
        ImmutableAuditService(self.db).append(
            entity_type="investment_eligibility",
            entity_id=item.id,
            action=f"investment.eligibility.{decision}",
            actor=actor,
            payload={
                "company_id": normalized_company_id,
                "score": health_score.score,
                "risk": health_score.risk,
                "recovery_plan_status": recovery_plan.status if recovery_plan else None,
            },
        )
        self.db.flush()
        return item

    def list_decisions(
        self,
        *,
        limit: int = 100,
        decision: str | None = None,
        company_id: str | None = None,
    ) -> list[InvestmentEligibilityDecision]:
        query = self.db.query(InvestmentEligibilityDecision)
        if decision:
            query = query.filter(InvestmentEligibilityDecision.decision == decision.strip().lower())
        if company_id:
            query = query.filter(InvestmentEligibilityDecision.company_id == company_id.strip())
        return query.order_by(InvestmentEligibilityDecision.decided_at.desc()).limit(limit).all()

    def _latest_health_score(self, company_id: str) -> HealthScore | None:
        return (
            self.db.query(HealthScore)
            .filter(HealthScore.company_id == company_id)
            .order_by(HealthScore.calculated_at.desc())
            .first()
        )

    def _latest_recovery_plan(self, company_id: str) -> RecoveryPlan | None:
        return (
            self.db.query(RecoveryPlan)
            .filter(RecoveryPlan.company_id == company_id)
            .order_by(RecoveryPlan.created_at.desc())
            .first()
        )

    def _resolve_decision(self, score: HealthScore, recovery_plan: RecoveryPlan | None) -> tuple[str, str]:
        plan_status = recovery_plan.status if recovery_plan else None

        if plan_status == "aggravated" or score.risk == "critical" or score.score <= 60:
            return (
                "restricted",
                "Score baixo/critico ou plano agravado. Empresa permanece restrita para investimento.",
            )

        if score.score >= 80 and plan_status not in OPEN_PLAN_STATUSES:
            return (
                "eligible",
                "Score alto e sem plano de recuperacao em aberto. Empresa elegivel para investimento.",
            )

        return (
            "monitoring",
            "Empresa em acompanhamento por score intermediario ou plano de recuperacao ativo.",
        )


def serialize_investment_decision(item: InvestmentEligibilityDecision) -> dict[str, Any]:
    return {
        "id": item.id,
        "company_id": item.company_id,
        "decision": item.decision,
        "rationale": item.rationale,
        "health_score_id": item.health_score_id,
        "recovery_plan_id": item.recovery_plan_id,
        "context": item.context or {},
        "decided_by": item.decided_by,
        "decided_at": item.decided_at.isoformat() if item.decided_at else None,
    }

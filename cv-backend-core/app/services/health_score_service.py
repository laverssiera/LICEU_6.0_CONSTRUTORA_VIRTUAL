from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.orchestration import AuditEvent, HealthScore


DIMENSIONS = ("financial", "operational", "compliance", "technology")
SEVERITY_PENALTY = {
    "LOW": 2,
    "MEDIUM": 6,
    "HIGH": 14,
    "CRITICAL": 24,
}


@dataclass
class CalculatedHealthScore:
    company_id: str
    score: int
    risk: str
    dimensions: dict[str, int]
    factors: dict[str, Any]
    calculated_from_events: int
    calculated_at: datetime


class HealthScoreService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def recalculate_company(
        self,
        company_id: str,
        *,
        lookback_days: int = 90,
        persist: bool = True,
    ) -> HealthScore:
        normalized_company_id = company_id.strip()
        if not normalized_company_id:
            raise ValueError("company_id vazio")

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=max(7, min(lookback_days, 365)))

        events = (
            self.db.query(AuditEvent)
            .filter(AuditEvent.entity_id == normalized_company_id)
            .filter(AuditEvent.detected_at >= cutoff)
            .order_by(AuditEvent.detected_at.desc())
            .all()
        )

        calculated = self._calculate(normalized_company_id, events, now)
        model = HealthScore(
            company_id=calculated.company_id,
            score=calculated.score,
            risk=calculated.risk,
            dimensions=calculated.dimensions,
            factors=calculated.factors,
            calculated_from_events=calculated.calculated_from_events,
            calculated_at=calculated.calculated_at,
        )

        if persist:
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)

        return model

    def list_scores(self, *, limit: int = 100, risk: str | None = None) -> list[HealthScore]:
        query = self.db.query(HealthScore)
        if risk:
            query = query.filter(HealthScore.risk == risk.strip().lower())
        return query.order_by(HealthScore.calculated_at.desc()).limit(limit).all()

    def list_history(self, company_id: str, *, limit: int = 20) -> list[HealthScore]:
        return (
            self.db.query(HealthScore)
            .filter(HealthScore.company_id == company_id)
            .order_by(HealthScore.calculated_at.desc())
            .limit(limit)
            .all()
        )

    def build_dashboard(
        self,
        *,
        limit: int = 100,
        risk: str | None = None,
        period_days: int = 90,
        deteriorating_only: bool = False,
    ) -> list[dict[str, Any]]:
        safe_period_days = max(7, min(period_days, 365))
        cutoff = datetime.now(timezone.utc) - timedelta(days=safe_period_days)

        query = self.db.query(HealthScore).filter(HealthScore.calculated_at >= cutoff)
        if risk:
            query = query.filter(HealthScore.risk == risk.strip().lower())

        snapshots = query.order_by(HealthScore.company_id.asc(), HealthScore.calculated_at.desc()).all()

        grouped: dict[str, list[HealthScore]] = {}
        for item in snapshots:
            grouped.setdefault(item.company_id, []).append(item)

        rows: list[dict[str, Any]] = []
        for company_id, company_snapshots in grouped.items():
            latest = company_snapshots[0]
            previous = company_snapshots[1] if len(company_snapshots) > 1 else None
            delta = latest.score - previous.score if previous else 0
            trend = "up" if delta > 0 else "down" if delta < 0 else "stable"
            is_deteriorating = delta < 0

            if deteriorating_only and not is_deteriorating:
                continue

            rows.append(
                {
                    "company_id": company_id,
                    "current": serialize_health_score(latest),
                    "previous": serialize_health_score(previous) if previous else None,
                    "trend": trend,
                    "delta": delta,
                    "is_deteriorating": is_deteriorating,
                    "snapshots_in_period": len(company_snapshots),
                }
            )

        rows.sort(key=lambda item: (not item["is_deteriorating"], item["current"]["score"]))
        return rows[:limit]

    def _calculate(self, company_id: str, events: list[AuditEvent], now: datetime) -> CalculatedHealthScore:
        penalties = {dimension: 0 for dimension in DIMENSIONS}
        severity_counter = {level.lower(): 0 for level in SEVERITY_PENALTY}

        for event in events:
            severity = (event.severity or "LOW").upper()
            penalty = SEVERITY_PENALTY.get(severity, SEVERITY_PENALTY["MEDIUM"])
            dimension = self._domain_to_dimension(event.audit_domain)
            penalties[dimension] += penalty
            severity_counter[severity.lower()] = severity_counter.get(severity.lower(), 0) + 1

        dimensions = {
            dimension: max(0, 100 - penalties[dimension])
            for dimension in DIMENSIONS
        }
        score = round(sum(dimensions.values()) / len(DIMENSIONS))
        risk = self._resolve_risk(score)
        factors = {
            "events_window_days": 90,
            "total_events": len(events),
            "severity_counter": severity_counter,
            "penalties": penalties,
            "weights": {
                "LOW": SEVERITY_PENALTY["LOW"],
                "MEDIUM": SEVERITY_PENALTY["MEDIUM"],
                "HIGH": SEVERITY_PENALTY["HIGH"],
                "CRITICAL": SEVERITY_PENALTY["CRITICAL"],
            },
        }

        return CalculatedHealthScore(
            company_id=company_id,
            score=score,
            risk=risk,
            dimensions=dimensions,
            factors=factors,
            calculated_from_events=len(events),
            calculated_at=now,
        )

    def _domain_to_dimension(self, domain: str | None) -> str:
        normalized = str(domain or "operations").strip().lower()
        if normalized == "financial":
            return "financial"
        if normalized == "compliance":
            return "compliance"
        if normalized == "technology":
            return "technology"
        return "operational"

    def _resolve_risk(self, score: int) -> str:
        if score >= 80:
            return "low"
        if score >= 60:
            return "medium"
        if score >= 40:
            return "high"
        return "critical"


def serialize_health_score(item: HealthScore) -> dict[str, Any]:
    return {
        "id": item.id,
        "company_id": item.company_id,
        "score": item.score,
        "risk": item.risk,
        "dimensions": item.dimensions or {},
        "factors": item.factors or {},
        "calculated_from_events": item.calculated_from_events,
        "calculated_at": item.calculated_at.isoformat() if item.calculated_at else None,
    }

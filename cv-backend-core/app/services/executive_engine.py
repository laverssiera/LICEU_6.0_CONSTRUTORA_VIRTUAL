from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.internal.event_bus import InMemoryEventBus, RedisEventBus
from app.services.capital_engine import allocate_budget
from app.services.strategic_core import strategic_decision


EXECUTIVE_MODES = {"AUTO", "SUPERVISED", "MANUAL"}
ALIGNED_ACTIONS = {
    "restructure_operations",
    "expand_region",
    "freeze_investments",
    "allocate_capital",
}


def build_state(
    metrics: dict[str, Any],
    autonomous_state: dict[str, Any] | None = None,
    innovation_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    autonomous_state = autonomous_state or {}
    innovation_state = innovation_state or {}

    kpis = metrics.get("kpis") or {}
    financeiro = metrics.get("financeiro") or {}
    performance = metrics.get("performance") or []
    monolith_status = metrics.get("monolith_status") or []

    estimated_revenue = float(kpis.get("estimated_revenue") or 0)
    pipeline_value = float(kpis.get("pipeline_value") or 0)
    conversion_rate = float(kpis.get("conversion_rate") or 0)

    revenue_growth = 0.0
    if pipeline_value > 0:
        revenue_growth = round((estimated_revenue - pipeline_value) / pipeline_value, 4)

    opportunity = 0.0
    active_leads = float(kpis.get("active_leads") or 0)
    if active_leads > 0:
        opportunity += min(active_leads / 100.0, 0.5)
    opportunity += min(conversion_rate / 100.0, 0.4)
    if innovation_state.get("critical_alerts", 0) == 0:
        opportunity += 0.1

    status_map = {str(item.get("name") or ""): item for item in monolith_status}
    monoliths = []
    for row in performance:
        name = str(row.get("source") or "unknown")
        revenue = float(row.get("revenue") or 0)
        cards = max(float(row.get("cards") or 1), 1)
        roi = revenue / cards
        risk = 0.3
        status = status_map.get(name, {}).get("status")
        if status in {"degraded", "down"}:
            risk = 0.8
        monoliths.append({"name": name, "roi": round(roi, 4), "risk": risk})

    state = {
        "revenue": estimated_revenue,
        "pipeline_value": pipeline_value,
        "revenue_growth": revenue_growth,
        "market_opportunity_score": round(min(max(opportunity, 0.0), 1.0), 4),
        "risk_level": autonomous_state.get("risk_level") or "medium",
        "active_deals": int(kpis.get("active_deals") or 0),
        "treasury_limit": round(max(float(financeiro.get("pipeline_value") or 0) * 0.2, 50000), 2),
        "legal_approved": False,
        "core_strategy": "real_estate_holding",
        "monoliths": monoliths,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return state


def decide(state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []

    for strategic in strategic_decision(state):
        decisions.append(_decision_from_payload(strategic))

    budget_map = allocate_budget(state)
    if budget_map:
        decisions.append(
            _decision_from_payload(
                {
                    "action": "allocate_capital",
                    "priority": "HIGH",
                    "target": "cea_invest",
                    "reason": "Redistribuição dinâmica de capital por ROI-risco.",
                    "budget_map": budget_map,
                    "budget": round(sum(budget_map.values()), 2),
                }
            )
        )

    return [apply_governance(item, state) for item in decisions]


def apply_governance(decision: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    action = decision.get("action")

    if action == "expand_region" and not bool(state.get("legal_approved")):
        blocked_reasons.append("legal_guard")

    budget = float(decision.get("payload", {}).get("budget") or 0)
    if budget > float(state.get("treasury_limit") or 0):
        blocked_reasons.append("treasury_guard")

    if action not in ALIGNED_ACTIONS:
        blocked_reasons.append("strategic_guard")

    decision["governance"] = {
        "juridicotech_allowed": "legal_guard" not in blocked_reasons,
        "cea_allowed": "treasury_guard" not in blocked_reasons,
        "strategic_allowed": "strategic_guard" not in blocked_reasons,
        "blocked_reasons": blocked_reasons,
    }

    decision["status"] = "blocked" if blocked_reasons else "planned"
    return decision


def orchestrate(
    *,
    decisions: list[dict[str, Any]],
    mode: str,
    bus: RedisEventBus | InMemoryEventBus,
    execute_action,
    action_cache: set[str],
) -> list[dict[str, Any]]:
    normalized_mode = (mode or "SUPERVISED").upper()
    results: list[dict[str, Any]] = []

    for decision in decisions:
        idempotency_key = build_idempotency_key(decision)
        record = {
            **decision,
            "mode": normalized_mode,
            "channel": resolve_channel(decision),
            "idempotency_key": idempotency_key,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        if idempotency_key in action_cache:
            results.append({**record, "status": "duplicate"})
            continue

        bus.publish(
            "executive.control",
            {
                "event_type": "executive.decision.proposed",
                "source": "john.executive",
                "payload": record,
            },
        )

        if record.get("governance", {}).get("blocked_reasons"):
            record["status"] = "blocked"
        elif normalized_mode == "AUTO":
            action_result = execute_action(record["action"], record.get("payload") or {})
            record["status"] = "executed"
            record["result"] = action_result
        elif normalized_mode == "SUPERVISED":
            record["status"] = "approval_required"
        else:
            record["status"] = "manual_hold"

        action_cache.add(idempotency_key)
        results.append(record)

    return results


def build_idempotency_key(decision: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "action": decision.get("action"),
            "target": decision.get("target"),
            "payload": decision.get("payload") or {},
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def resolve_channel(decision: dict[str, Any]) -> str:
    target = str(decision.get("target") or "ecosystem").replace("-", "_")
    if target == "all_monoliths":
        return "executive.broadcast"
    return f"{target}.executive"


def _decision_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": "EXECUTIVE",
        "action": payload.get("action"),
        "target": payload.get("target") or "all_monoliths",
        "priority": payload.get("priority") or "HIGH",
        "reason": payload.get("reason") or "Execução estratégica",
        "payload": {
            "target": payload.get("target") or "all_monoliths",
            "reason": payload.get("reason") or "Execução estratégica",
            "region": payload.get("region"),
            "budget": payload.get("budget"),
            "budget_map": payload.get("budget_map"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

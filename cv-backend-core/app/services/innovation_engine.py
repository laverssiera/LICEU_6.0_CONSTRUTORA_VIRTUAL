from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.internal.event_bus import InMemoryEventBus, RedisEventBus


INNOVATION_MODES = {"AUTO", "SUPERVISED", "RESTRICTED"}
ALIGNED_CATEGORIES = {"real_estate", "retail_real_estate", "legal_ops", "finance_ops"}


def build_state(metrics: dict[str, Any], autonomous_state: dict[str, Any] | None = None) -> dict[str, Any]:
    kpis = metrics.get("kpis") or {}
    financeiro = metrics.get("financeiro") or {}
    performance = metrics.get("performance") or []
    risk_signals = metrics.get("risk_signals") or []
    autonomous_state = autonomous_state or {}

    pipeline_value = float(kpis.get("pipeline_value") or 0)
    estimated_revenue = float(kpis.get("estimated_revenue") or 0)
    available_budget = round(max(pipeline_value * 0.03, estimated_revenue * 0.05, 25000), 2)
    budget_guard_limit = round(max(available_budget * 0.4, 10000), 2)
    top_monolith = performance[0].get("source") if performance else autonomous_state.get("top_monolith", "archimedes")
    bottlenecks = list(dict.fromkeys(autonomous_state.get("bottlenecks") or []))
    risk_level = autonomous_state.get("risk_level") or ("high" if risk_signals else "low")

    return {
        "available_budget": available_budget,
        "budget_guard_limit": budget_guard_limit,
        "risk_level": risk_level,
        "critical_alerts": len(risk_signals),
        "top_monolith": top_monolith,
        "strategic_alignment_required": True,
        "bottlenecks": bottlenecks,
        "estimated_revenue": estimated_revenue,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def decide(state: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    kpis = metrics.get("kpis") or {}
    performance = metrics.get("performance") or []
    risk_signals = metrics.get("risk_signals") or []
    opportunities: list[dict[str, Any]] = []

    opportunities.append(
        _idea(
            name="Micro Commercial Units",
            category="retail_real_estate",
            confidence=0.82 if int(kpis.get("active_leads") or 0) >= 1 else 0.61,
            estimated_budget=min(state["budget_guard_limit"], 18000.0),
            target="archimedes",
            expected_roi=1.24,
            rationale="Demanda ativa e pipeline imobiliário permitem teste controlado de unidades comerciais compactas.",
        )
    )

    if float(kpis.get("conversion_rate") or 0) < 12:
        opportunities.append(
            _idea(
                name="Legal Express Desk",
                category="legal_ops",
                confidence=0.77,
                estimated_budget=min(state["budget_guard_limit"], 12000.0),
                target="juridicotech",
                expected_roi=1.18,
                rationale="Fila jurídica e conversão pressionada indicam ganho rápido com trilha expressa de contratos.",
            )
        )

    if performance and performance[0].get("source") == "archimedes" and state.get("risk_level") != "high":
        opportunities.append(
            _idea(
                name="Investor Liquidity Window",
                category="finance_ops",
                confidence=0.74,
                estimated_budget=min(state["budget_guard_limit"], 16000.0),
                target="cea_invest",
                expected_roi=1.15,
                rationale="Melhor monólito performando suporta experimento de liquidez com governança financeira.",
            )
        )

    if risk_signals:
        opportunities.append(
            _idea(
                name="Viral Social Commerce",
                category="brand_adjacent",
                confidence=0.68,
                estimated_budget=max(state["budget_guard_limit"] * 1.4, 35000.0),
                target="gamemkt",
                expected_roi=1.05,
                rationale="Hipótese agressiva de aquisição; propositalmente sujeita a bloqueio de governança em ambiente sensível.",
            )
        )

    return [apply_governance(item, state) for item in opportunities]


def apply_governance(idea: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    blocked_reasons: list[str] = []

    if float(idea.get("estimated_budget") or 0) > float(state.get("budget_guard_limit") or 0):
        blocked_reasons.append("budget_guard")

    if idea.get("category") not in ALIGNED_CATEGORIES:
        blocked_reasons.append("strategic_alignment")

    if state.get("risk_level") == "high" and idea.get("category") in {"retail_real_estate", "brand_adjacent"}:
        blocked_reasons.append("risk_lock")

    if "legal" in (state.get("bottlenecks") or []) and idea.get("category") == "brand_adjacent":
        blocked_reasons.append("compliance_guard")

    idea["governance"] = {
        "budget_allowed": "budget_guard" not in blocked_reasons,
        "compliance_allowed": "compliance_guard" not in blocked_reasons,
        "alignment_allowed": "strategic_alignment" not in blocked_reasons,
        "risk_allowed": "risk_lock" not in blocked_reasons,
        "blocked_reasons": blocked_reasons,
    }
    idea["status"] = "blocked" if blocked_reasons else "testing"
    return idea


def orchestrate(
    *,
    ideas: list[dict[str, Any]],
    mode: str,
    bus: RedisEventBus | InMemoryEventBus,
    execute_action,
    action_cache: set[str],
) -> list[dict[str, Any]]:
    normalized_mode = (mode or "SUPERVISED").upper()
    results: list[dict[str, Any]] = []

    for idea in ideas:
        record = dict(idea)
        record["mode"] = normalized_mode
        record["idempotency_key"] = build_idempotency_key(record)

        if record["idempotency_key"] in action_cache:
            results.append({**record, "status": "duplicate"})
            continue

        bus.publish(
            "innovation.engine",
            {
                "event_type": "innovation.engine.proposed",
                "source": "john.innovation",
                "payload": record,
            },
        )

        if record.get("governance", {}).get("blocked_reasons"):
            record["status"] = "blocked"
        elif normalized_mode == "AUTO":
            action_result = execute_action("launch_experiment", record.get("payload") or {})
            record["status"] = "executed"
            record["result"] = action_result
            bus.publish(
                "experiment.launch",
                {
                    "event_type": "experiment.launch",
                    "source": "john.innovation",
                    "payload": record,
                },
            )
        elif normalized_mode == "SUPERVISED":
            record["status"] = "approval_required"
        else:
            record["status"] = "insight_only"

        action_cache.add(record["idempotency_key"])
        results.append(record)

    return results


def build_idempotency_key(item: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "name": item.get("name"),
            "target": item.get("target"),
            "budget": item.get("estimated_budget"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _idea(
    *,
    name: str,
    category: str,
    confidence: float,
    estimated_budget: float,
    target: str,
    expected_roi: float,
    rationale: str,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": "INNOVATION",
        "name": name,
        "category": category,
        "confidence": round(confidence, 2),
        "estimated_budget": round(estimated_budget, 2),
        "target": target,
        "expected_roi": round(expected_roi, 2),
        "rationale": rationale,
        "status": "testing",
        "payload": {
            "experiment_name": name,
            "type": category,
            "target": target,
            "budget": round(estimated_budget, 2),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
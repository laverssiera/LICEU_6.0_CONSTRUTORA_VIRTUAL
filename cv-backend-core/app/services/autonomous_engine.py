from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.internal.event_bus import InMemoryEventBus, RedisEventBus


AUTONOMOUS_MODES = {"AUTO", "SEMI", "MANUAL"}


def build_state(metrics: dict[str, Any]) -> dict[str, Any]:
    kpis = metrics.get("kpis") or {}
    monolith_status = metrics.get("monolith_status") or []
    performance = metrics.get("performance") or []
    risk_signals = metrics.get("risk_signals") or []

    bottlenecks: list[str] = []
    if int(kpis.get("juridico_cards") or 0) > 0:
        bottlenecks.append("legal")
    if any((item.get("status") in {"degraded", "down"}) for item in monolith_status):
        bottlenecks.append("operations")
    if float(kpis.get("conversion_rate") or 0) < 10:
        bottlenecks.append("marketing")
    if float(metrics.get("financeiro", {}).get("accounts_receivable") or 0) > float(metrics.get("financeiro", {}).get("estimated_revenue") or 0):
        bottlenecks.append("finance")

    high_risk_cards = int(kpis.get("high_risk_cards") or 0)
    critical_alerts = len(risk_signals)
    risk_level = "low"
    if high_risk_cards > 0 or critical_alerts >= 3:
        risk_level = "high"
    elif critical_alerts > 0:
        risk_level = "medium"

    top_monolith = performance[0].get("source") if performance else "unknown"
    state = {
        "revenue": float(kpis.get("estimated_revenue") or 0),
        "pipeline_value": float(kpis.get("pipeline_value") or 0),
        "risk_level": risk_level,
        "active_deals": int(kpis.get("active_deals") or 0),
        "active_leads": int(kpis.get("active_leads") or 0),
        "conversion_rate": round(float(kpis.get("conversion_rate") or 0) / 100, 4),
        "bottlenecks": sorted(set(bottlenecks)),
        "top_monolith": top_monolith,
        "critical_alerts": critical_alerts,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return state


def decide(state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []

    if state.get("risk_level") == "high":
        decisions.append(
            _decision("reduce_exposure", "all_monoliths", "Risco global alto exige redução de exposição", "CRITICAL")
        )

    if float(state.get("conversion_rate") or 0) < 0.1:
        decisions.append(
            _decision("boost_marketing", "gamemkt", "Conversão abaixo do limiar exige reforço de aquisição", "HIGH")
        )

    bottlenecks = set(state.get("bottlenecks") or [])
    if "legal" in bottlenecks:
        decisions.append(
            _decision("prioritize_legal", "juridicotech", "Gargalo jurídico detectado no pipeline", "CRITICAL")
        )

    if "finance" in bottlenecks:
        decisions.append(
            _decision("tighten_finance", "hubbackoffice", "Exposição financeira acima do desejado", "HIGH")
        )

    if state.get("active_deals", 0) > 20 and state.get("risk_level") == "low":
        decisions.append(
            _decision("increase_prices", "archimedes", "Alta demanda com risco controlado permite ajuste de preço", "MEDIUM")
        )

    return decisions


def orchestrate(
    *,
    decisions: list[dict[str, Any]],
    mode: str,
    bus: RedisEventBus | InMemoryEventBus,
    execute_action,
    action_cache: set[str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    normalized_mode = (mode or "SEMI").upper()

    for decision in decisions:
        idempotency_key = build_idempotency_key(decision)
        if idempotency_key in action_cache:
            results.append({
                **decision,
                "status": "duplicate",
                "mode": normalized_mode,
                "idempotency_key": idempotency_key,
            })
            continue

        channel = resolve_channel(decision)
        record = {
            **decision,
            "mode": normalized_mode,
            "channel": channel,
            "idempotency_key": idempotency_key,
            "status": "suggested",
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        bus.publish(
            channel,
            {
                "event_type": "autonomous.decision.dispatched",
                "source": "john.autonomous",
                "payload": record,
            },
        )

        if normalized_mode == "AUTO":
            action_result = execute_action(decision["action"], decision.get("payload") or {})
            record["status"] = "executed"
            record["result"] = action_result
        elif normalized_mode == "SEMI":
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
        return "ecosystem.control"
    return f"{target}.priority"


def _decision(action: str, target: str, reason: str, priority: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": "AUTONOMOUS",
        "action": action,
        "target": target,
        "reason": reason,
        "priority": priority,
        "payload": {"target": target, "reason": reason},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
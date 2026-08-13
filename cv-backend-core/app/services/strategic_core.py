from __future__ import annotations

from typing import Any


def strategic_decision(state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []

    if float(state.get("revenue_growth") or 0) < 0:
        decisions.append(
            {
                "action": "restructure_operations",
                "priority": "HIGH",
                "target": "all_monoliths",
                "reason": "Queda de receita exige reestruturação operacional.",
            }
        )

    if float(state.get("market_opportunity_score") or 0) > 0.8:
        decisions.append(
            {
                "action": "expand_region",
                "priority": "HIGH",
                "target": "archimedes",
                "region": "new_market",
                "reason": "Score de oportunidade elevado indica expansão regional.",
            }
        )

    if state.get("risk_level") == "high":
        decisions.append(
            {
                "action": "freeze_investments",
                "priority": "CRITICAL",
                "target": "cea_invest",
                "reason": "Risco elevado exige congelamento de investimentos.",
            }
        )

    return decisions

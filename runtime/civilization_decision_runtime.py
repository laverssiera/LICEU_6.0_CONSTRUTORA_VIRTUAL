from __future__ import annotations

from typing import Any, Dict, List


class CivilizationDecisionRuntime:
    """Converte score e sinais de risco em decisoes de operacao."""

    def decide(self, score_payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        score = float(score_payload.get("civilization_score", 0.0))
        alerts = state.get("critical_alerts", [])

        mode = "RECOVER"
        actions: List[str] = ["freeze_non_critical_rollouts", "open_war_room"]

        if score >= 0.85 and not alerts:
            mode = "EXPAND"
            actions = [
                "accelerate_missions",
                "expand_construction_projects",
                "increase_scientific_experiments",
            ]
        elif score >= 0.65:
            mode = "STABILIZE"
            actions = [
                "preserve_current_throughput",
                "prioritize_predictive_maintenance",
            ]
        elif score >= 0.45:
            mode = "DEFEND"
            actions = [
                "reduce_operational_risk",
                "review_financial_exposure",
                "tighten_change_approval",
            ]

        return {
            "decision_mode": mode,
            "recommended_actions": actions,
            "critical_alerts_count": len(alerts),
        }


decision_runtime = CivilizationDecisionRuntime()

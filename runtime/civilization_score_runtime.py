from __future__ import annotations

import re
from typing import Any, Dict


class CivilizationScoreRuntime:
    """Calcula um score agregado de saude operacional da civilizacao."""

    def _normalize(self, value: float, floor: float, ceiling: float) -> float:
        if ceiling <= floor:
            return 0.0
        raw = (value - floor) / (ceiling - floor)
        return max(0.0, min(1.0, raw))

    def _parse_money_billions(self, raw: str) -> float:
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw or "")
        if not match:
            return 0.0
        return float(match.group(1))

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        metrics = state.get("metrics", {})

        health_pct = str(metrics.get("federation_health", "0%")).replace("%", "")
        health_value = float(health_pct) if health_pct else 0.0

        alerts = state.get("critical_alerts", [])
        exposure_b = self._parse_money_billions(str(metrics.get("financial_exposure", "$0B")))

        availability = self._normalize(health_value, 85.0, 100.0)
        execution = self._normalize(float(metrics.get("missions_active", 0)), 5.0, 50.0)
        resilience = 1.0 - self._normalize(float(len(alerts)), 0.0, 10.0)
        risk_control = 1.0 - self._normalize(exposure_b, 1.0, 8.0)

        score = (
            availability * 0.35
            + execution * 0.25
            + resilience * 0.25
            + risk_control * 0.15
        )

        return {
            "civilization_score": round(score, 4),
            "dimensions": {
                "availability": round(availability, 4),
                "execution": round(execution, 4),
                "resilience": round(resilience, 4),
                "risk_control": round(risk_control, 4),
            },
            "status": state.get("civilization_status", "UNKNOWN"),
        }


score_runtime = CivilizationScoreRuntime()

from __future__ import annotations

from typing import Any, Dict, List, Optional

from runtime.civilization_sensor_runtime import CivilizationSensorRuntime


class CivilizationPredictionRuntime:
    """Motor de predicao heuristica para o digital twin."""

    def __init__(self, sensor_runtime: Optional[CivilizationSensorRuntime] = None) -> None:
        self._sensor_runtime = sensor_runtime or CivilizationSensorRuntime()

    def predict(
        self,
        state: Dict[str, Any],
        twin_id: str,
        horizon_minutes: int = 60,
    ) -> Dict[str, Any]:
        safe_horizon = max(1, min(horizon_minutes, 1440))
        recent = self._sensor_runtime.list_recent(twin_id=twin_id, limit=200)

        values = [self._to_float(item.get("value")) for item in recent]
        values = [item for item in values if item is not None]

        avg_value = round(sum(values) / len(values), 4) if values else None
        latest_value = values[-1] if values else None
        trend = "stable"
        if values and len(values) >= 2:
            if values[-1] > values[0]:
                trend = "up"
            elif values[-1] < values[0]:
                trend = "down"

        alerts_count = len(state.get("sensors", {}))
        volatility = 0.0
        if values:
            volatility = max(values) - min(values)

        risk_score = min(1.0, (alerts_count * 0.05) + (volatility * 0.02))
        predicted_status = "STABLE"
        if risk_score >= 0.75:
            predicted_status = "CRITICAL"
        elif risk_score >= 0.45:
            predicted_status = "ATTENTION"

        return {
            "twin_id": twin_id,
            "horizon_minutes": safe_horizon,
            "predicted_status": predicted_status,
            "risk_score": round(risk_score, 4),
            "trend": trend,
            "latest_value": latest_value,
            "average_value": avg_value,
            "sample_size": len(values),
            "recommendations": self._build_recommendations(predicted_status, trend),
        }

    def _to_float(self, raw: Any) -> Optional[float]:
        try:
            return float(raw)
        except Exception:
            return None

    def _build_recommendations(self, predicted_status: str, trend: str) -> List[str]:
        if predicted_status == "CRITICAL":
            return [
                "open_incident_bridge",
                "increase_sensor_sampling_rate",
                "run_emergency_stabilization",
            ]
        if predicted_status == "ATTENTION":
            return [
                "schedule_predictive_maintenance",
                "tighten_governance_thresholds",
            ]
        if trend == "up":
            return ["continue_monitoring", "validate_capacity_headroom"]
        return ["maintain_baseline_monitoring"]


prediction_runtime = CivilizationPredictionRuntime()

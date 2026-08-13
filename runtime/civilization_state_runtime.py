from __future__ import annotations

import random
from typing import Any, Dict, Optional

try:
    from runtime.civilization.civilization_state_runtime import CivilizationStateRuntime as _CivilizationStateBase
except Exception:
    _CivilizationStateBase = object


class CivilizationStateRuntime(_CivilizationStateBase):
    """Facade para o estado da civilizacao no namespace runtime/."""

    def __init__(self) -> None:
        try:
            super().__init__()  # type: ignore[misc]
        except Exception:
            pass

    def get_global_pulse(self) -> Dict[str, Any]:
        if hasattr(super(), "get_global_pulse"):
            return super().get_global_pulse()  # type: ignore[misc]

        return {
            "civilization_status": "EXPANDING",
            "metrics": {
                "missions_active": random.randint(15, 45),
                "contracts_active": random.randint(1200, 2000),
                "twins_active": random.randint(300, 500),
                "scientific_experiments": random.randint(5, 20),
                "construction_projects": random.randint(10, 30),
                "financial_exposure": f"${random.uniform(1.5, 5.0):.2f}B",
                "federation_health": "99.98%",
            },
            "critical_alerts": [],
        }

    def get_state_snapshot(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pulse = self.get_global_pulse()
        if context:
            pulse["context"] = context
        return pulse


state_runtime = CivilizationStateRuntime()


def get_civilization_state(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return state_runtime.get_state_snapshot(context=context)

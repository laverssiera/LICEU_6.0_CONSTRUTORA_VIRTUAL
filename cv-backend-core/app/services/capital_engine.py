from __future__ import annotations

from typing import Any


def allocate_budget(state: dict[str, Any]) -> dict[str, float]:
    allocation: dict[str, float] = {}
    monoliths = state.get("monoliths") or []

    for monolith in monoliths:
        name = str(monolith.get("name") or "unknown")
        roi = float(monolith.get("roi") or 0)
        risk = float(monolith.get("risk") or 0)
        score = roi - risk
        allocation[name] = round(max(score * 10000, 0), 2)

    return allocation

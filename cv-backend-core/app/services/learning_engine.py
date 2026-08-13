from __future__ import annotations

from typing import Any


def learn(result: dict[str, Any], memory: dict[str, float]) -> dict[str, Any]:
    decision = str(result.get("decision") or result.get("action") or "unknown")
    success = bool(result.get("success"))
    current = float(memory.get(decision) or 0.5)

    delta = 0.05 if success else -0.07
    updated = min(1.0, max(0.0, current + delta))
    memory[decision] = round(updated, 4)

    return {
        "decision": decision,
        "success": success,
        "previous_confidence": round(current, 4),
        "updated_confidence": memory[decision],
    }

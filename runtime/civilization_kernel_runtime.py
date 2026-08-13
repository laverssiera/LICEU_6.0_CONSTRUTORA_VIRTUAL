from __future__ import annotations

from typing import Any, Dict, Optional

from runtime.civilization_decision_runtime import decision_runtime
from runtime.civilization_score_runtime import score_runtime
from runtime.civilization_snapshot_runtime import snapshot_runtime
from runtime.civilization_state_runtime import state_runtime


class CivilizationKernelRuntime:
    """Nucleo de orquestracao do ciclo de avaliacao da civilizacao."""

    def run_cycle(
        self,
        external_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        state = external_state or state_runtime.get_global_pulse()
        score = score_runtime.evaluate(state)
        decision = decision_runtime.decide(score, state)
        snapshot = snapshot_runtime.capture(
            state=state,
            score=score,
            decision=decision,
            metadata=metadata,
        )

        return {
            "state": state,
            "score": score,
            "decision": decision,
            "snapshot": snapshot,
        }


kernel_runtime = CivilizationKernelRuntime()


def run_kernel_cycle(
    external_state: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return kernel_runtime.run_cycle(external_state=external_state, metadata=metadata)

from __future__ import annotations

from typing import Any, Dict, List, Optional

from runtime.civilization_kernel_runtime import kernel_runtime


class CivilizationPipelineRuntime:
    """Executa multiplos ciclos do kernel e agrega resultados."""

    def run(
        self,
        pulses: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        results = []
        mode_distribution: Dict[str, int] = {}

        for index, pulse in enumerate(pulses):
            cycle = kernel_runtime.run_cycle(
                external_state=pulse,
                metadata={"sequence": index, **(metadata or {})},
            )
            mode = cycle["decision"]["decision_mode"]
            mode_distribution[mode] = mode_distribution.get(mode, 0) + 1
            results.append(cycle)

        return {
            "cycles": len(results),
            "mode_distribution": mode_distribution,
            "results": results,
        }


pipeline_runtime = CivilizationPipelineRuntime()


def run_civilization_pipeline(
    pulses: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return pipeline_runtime.run(pulses=pulses, metadata=metadata)

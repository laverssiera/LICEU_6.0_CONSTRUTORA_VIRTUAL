# Planet Runtime
# Runtime planetario

from runtime.activation.planetary_activation_runtime import PlanetaryActivationRuntime
from runtime.planetary.autonomous.autonomous_planetary_coordination import (
    AutonomousPlanetaryCoordination,
)
from runtime.planetary.autonomous.sovereign_planetary_scheduler import (
    SovereignPlanetaryScheduler,
)


class PlanetRuntime:
    def __init__(
        self,
        cycle_interval_seconds=60,
        max_cycles=1,
        scheduler=None,
        coordinator=None,
        activator=None,
    ):
        self.cycle_interval_seconds = cycle_interval_seconds
        self.max_cycles = max_cycles
        self.scheduler = scheduler or SovereignPlanetaryScheduler()
        self.coordinator = coordinator or AutonomousPlanetaryCoordination()
        self.activator = activator or PlanetaryActivationRuntime()

    def _run_cycle(self, cycle_number):
        steps = []

        if self.activator:
            activation_result = self.activator.activate()
            steps.append({"step": "activate", "result": activation_result})

        if self.scheduler:
            scheduler_result = self.scheduler.schedule()
            steps.append({"step": "schedule", "result": scheduler_result})

        if self.coordinator:
            coordination_result = self.coordinator.coordinate()
            steps.append({"step": "coordinate", "result": coordination_result})

        return {"cycle": cycle_number, "steps": steps}

    def run(self, cycles=None):
        total_cycles = self.max_cycles if cycles is None else cycles

        if total_cycles < 1:
            raise ValueError("cycles must be >= 1")

        operations = []
        for cycle in range(1, total_cycles + 1):
            operations.append(self._run_cycle(cycle))

        return {
            "status": "completed",
            "total_cycles": total_cycles,
            "cycle_interval_seconds": self.cycle_interval_seconds,
            "operations": operations,
        }

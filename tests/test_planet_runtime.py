from runtime.planetary.planet_runtime import PlanetRuntime


class _FakeActivator:
    def __init__(self):
        self.calls = 0

    def activate(self):
        self.calls += 1
        return "activated"


class _FakeScheduler:
    def __init__(self):
        self.calls = 0

    def schedule(self):
        self.calls += 1
        return "scheduled"


class _FakeCoordinator:
    def __init__(self):
        self.calls = 0

    def coordinate(self):
        self.calls += 1
        return "coordinated"


def test_planet_runtime_runs_all_components_for_each_cycle():
    activator = _FakeActivator()
    scheduler = _FakeScheduler()
    coordinator = _FakeCoordinator()

    runtime = PlanetRuntime(
        cycle_interval_seconds=5,
        max_cycles=2,
        activator=activator,
        scheduler=scheduler,
        coordinator=coordinator,
    )

    report = runtime.run()

    assert report["status"] == "completed"
    assert report["total_cycles"] == 2
    assert report["cycle_interval_seconds"] == 5
    assert len(report["operations"]) == 2

    assert activator.calls == 2
    assert scheduler.calls == 2
    assert coordinator.calls == 2


def test_planet_runtime_rejects_invalid_cycle_count():
    runtime = PlanetRuntime()

    try:
        runtime.run(cycles=0)
        assert False, "run(cycles=0) should raise ValueError"
    except ValueError as exc:
        assert str(exc) == "cycles must be >= 1"

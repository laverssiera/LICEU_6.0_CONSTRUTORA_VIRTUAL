from fastapi.testclient import TestClient

from runtime.kernel_app import app

client = TestClient(app)


def test_planet_runtime_run_endpoint_executes_cycles():
    response = client.post(
        "/planetary/runtime/run",
        json={"cycles": 2, "cycle_interval_seconds": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["total_cycles"] == 2
    assert data["cycle_interval_seconds"] == 5
    assert len(data["operations"]) == 2


def test_planet_runtime_run_endpoint_rejects_invalid_cycles():
    response = client.post(
        "/planetary/runtime/run",
        json={"cycles": 0, "cycle_interval_seconds": 5},
    )

    assert response.status_code == 422

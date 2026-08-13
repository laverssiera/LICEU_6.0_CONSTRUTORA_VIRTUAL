from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_civilization_twin_update_and_state():
    response = client.post(
        "/civilization/twin/update",
        json={
            "twin_id": "twin-alpha",
            "status": "ACTIVE",
            "attributes": {"region": "sudeste"},
            "metrics": {"energy": 87.5},
            "geospatial": {"latitude": -23.5505, "longitude": -46.6333, "altitude": 760},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "updated"
    assert payload["twin"]["state"]["twin_id"] == "twin-alpha"
    assert payload["twin"]["state"]["attributes"]["region"] == "sudeste"

    state_response = client.get("/civilization/twin/state?twin_id=twin-alpha")
    assert state_response.status_code == 200
    state_payload = state_response.json()
    assert state_payload["status"] == "ok"
    assert state_payload["twin"]["state"]["twin_id"] == "twin-alpha"
    assert state_payload["twin"]["state"]["cesium_entity"] is not None


def test_civilization_sensor_predict_and_graph():
    sensor_response = client.post(
        "/civilization/sensors",
        json={
            "twin_id": "twin-beta",
            "sensor_id": "sensor-temp-001",
            "metric": "temperature",
            "value": 42.3,
            "unit": "c",
        },
    )
    assert sensor_response.status_code == 200
    sensor_payload = sensor_response.json()
    assert sensor_payload["status"] == "ingested"
    assert sensor_payload["sensor_event"]["twin_id"] == "twin-beta"

    predict_response = client.post(
        "/civilization/predict",
        json={"twin_id": "twin-beta", "horizon_minutes": 120},
    )
    assert predict_response.status_code == 200
    predict_payload = predict_response.json()
    assert predict_payload["status"] == "predicted"
    assert predict_payload["prediction"]["twin_id"] == "twin-beta"
    assert "risk_score" in predict_payload["prediction"]

    graph_response = client.get("/civilization/graph?limit=50")
    assert graph_response.status_code == 200
    graph_payload = graph_response.json()
    assert graph_payload["status"] == "ok"
    assert "nodes" in graph_payload["graph"]
    assert "edges" in graph_payload["graph"]

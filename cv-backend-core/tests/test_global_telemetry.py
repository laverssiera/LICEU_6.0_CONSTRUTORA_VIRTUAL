import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "cv-backend-core"
SCHEMA_SRC = ROOT / "liceu-core-schemas" / "src"
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(SCHEMA_SRC))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_global_telemetry.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_telemetry_global_exposes_15_monoliths():
    response = client.get("/telemetry/global")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_monolitos"] == 15
    assert "detalhes" in payload
    assert "john_brasileiro" in payload["detalhes"]


def test_telemetry_global_stabilizes_virtual_core_pillars():
    response = client.get("/telemetry/global")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ativos"] >= 4
    assert "ONLINE" in payload["detalhes"]["core_os"]
    assert "ONLINE" in payload["detalhes"]["archimedes"]
    assert "ONLINE" in payload["detalhes"]["academia_saber"]
    assert "ONLINE" in payload["detalhes"]["john_brasileiro"]


def test_john_status_report_returns_message():
    response = client.get("/john/status-report")

    assert response.status_code == 200
    payload = response.json()
    assert "john_msg" in payload
    assert len(payload["john_msg"]) > 10

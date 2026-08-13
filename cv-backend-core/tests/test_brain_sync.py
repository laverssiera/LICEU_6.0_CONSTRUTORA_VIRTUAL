import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "cv-backend-core"
SCHEMA_SRC = ROOT / "liceu-core-schemas" / "src"
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(SCHEMA_SRC))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_brain_sync.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_brain_sync_generates_pulse_and_training_plan():
    response = client.post(
        "/brain/sync",
        json={
            "project_code": "OBRA-PILOTO-001",
            "discipline": "estrutura",
            "reported_by": "concrete-vision-ai",
            "artifact_uri": "s3://liceu/obras/piloto-001/frame-77.jpg",
            "observations": [
                "fissura horizontal no encontro da laje",
                "infiltracao recorrente na parede tecnica",
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "synced"
    assert payload["source"] == "concrete-vision-ai"
    assert payload["pathology_report"]["total_findings"] >= 1
    assert payload["cognitive_pulse"]["pillar"] == "joh_brasileiro"
    assert payload["academy_training"]["academy"] == "academia_saber"
    assert payload["academy_training"]["module_count"] >= 1
    assert payload["academy_training"]["priority"] in {"alta", "moderada", "baixa"}
    assert len(payload["academy_training"]["checklist"]) >= 1
    assert "mentor" in payload["academy_training"]
    assert payload["event_delivery"]["listener"] == "joh_brasileiro"

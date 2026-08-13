from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

SCHEMA_SRC = Path(__file__).resolve().parents[3] / "liceu-core-schemas" / "src"
if SCHEMA_SRC.exists() and str(SCHEMA_SRC) not in sys.path:
    sys.path.insert(0, str(SCHEMA_SRC))

from liceu_core_schemas import CognitivePulse, PulseSeverity  # type: ignore


class BrainSyncRequest(BaseModel):
    project_code: str = Field(min_length=3, max_length=64)
    discipline: str = Field(min_length=3, max_length=64)
    reported_by: str = Field(default="concrete-vision-ai", min_length=3, max_length=64)
    artifact_uri: str | None = None
    observations: list[str] = Field(default_factory=list)


def build_cognitive_pulse(report: dict[str, Any], payload: BrainSyncRequest) -> CognitivePulse:
    severity_map = {"info": 0, "warning": 1, "critical": 2}
    severity_name = max(
        (item.get("severity", "info") for item in report.get("findings", [])),
        key=lambda value: severity_map.get(value, 0),
        default="info",
    )

    severity = {
        "critical": PulseSeverity.CRITICAL,
        "warning": PulseSeverity.WARNING,
    }.get(severity_name, PulseSeverity.INFO)

    summary = report.get("summary", "Sem anomalias críticas no momento.")
    recommendation = report.get("primary_action", "Monitorar o processo e registrar feedback.")

    return CognitivePulse(
        pillar="joh_brasileiro",
        severity=severity,
        message=f"John traduzido: {summary}",
        recommended_action=recommendation,
        sentiment_index=-0.35 if severity == PulseSeverity.CRITICAL else -0.1,
        tags=[payload.discipline, payload.project_code.lower(), "aprendizado_continuo"],
        context={
            "project_code": payload.project_code,
            "discipline": payload.discipline,
            "reported_by": payload.reported_by,
            "artifact_uri": payload.artifact_uri,
            "top_pathology": report.get("top_pathology"),
        },
    )

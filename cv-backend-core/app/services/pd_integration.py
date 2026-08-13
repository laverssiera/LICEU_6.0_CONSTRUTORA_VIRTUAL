from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.initiative import Initiative
from app.models.pd_process import PDProcess


class PDIntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def should_create_process(self, initiative: Initiative) -> bool:
        normalized_type = (initiative.initiative_type or "").strip().lower()
        text = f"{initiative.name} {initiative.description}".lower()
        return normalized_type in {"process", "training"} and any(
            keyword in text for keyword in ["p&d", "pd", "pesquisa", "inov", "ia", "prototipo", "prototype"]
        )

    def sync_process(self, initiative: Initiative) -> dict[str, Any] | None:
        if not self.should_create_process(initiative):
            return None

        latest = (
            self.db.query(PDProcess)
            .filter(PDProcess.initiative_id == initiative.id)
            .order_by(PDProcess.version.desc())
            .first()
        )

        if latest and latest.title == initiative.name and latest.description == initiative.description:
            return {
                "action": "noop",
                "process": latest,
                "version": latest.version,
            }

        next_version = 1 if latest is None else latest.version + 1
        process = PDProcess(
            initiative_id=initiative.id,
            version=next_version,
            process_code=f"PD-{initiative.id:05d}",
            title=initiative.name,
            description=initiative.description,
            process_type="research",
            target_monolith="pdi_ia",
            status="draft",
        )
        self.db.add(process)
        self.db.commit()
        self.db.refresh(process)
        return {
            "action": "created" if next_version == 1 else "versioned",
            "process": process,
            "version": process.version,
        }

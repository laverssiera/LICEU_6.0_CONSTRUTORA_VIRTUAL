from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.initiative import Initiative
from app.models.plan import Plan
from app.models.task import Task


TASK_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "process": [
        {"title": "Mapear fluxo atual", "description": "Diagnosticar o processo vigente e gargalos.", "priority": "high"},
        {"title": "Definir processo alvo", "description": "Documentar o fluxo futuro com responsáveis.", "priority": "high"},
        {"title": "Implantar rotina operacional", "description": "Executar a adoção do processo no time.", "priority": "normal"},
    ],
    "training": [
        {"title": "Levantar competências", "description": "Identificar lacunas de conhecimento da equipe.", "priority": "high"},
        {"title": "Montar trilha de treinamento", "description": "Estruturar conteúdo, sequência e critérios de conclusão.", "priority": "high"},
        {"title": "Aplicar capacitação", "description": "Executar a trilha e acompanhar adesão.", "priority": "normal"},
    ],
    "execution": [
        {"title": "Planejar execução", "description": "Definir cronograma, recursos e responsáveis da entrega.", "priority": "high"},
        {"title": "Executar piloto", "description": "Realizar primeira entrega controlada do plano.", "priority": "high"},
        {"title": "Validar rollout", "description": "Mensurar resultado e liberar expansão operacional.", "priority": "normal"},
    ],
    "financial": [
        {"title": "Consolidar premissas financeiras", "description": "Reunir dados-base para análise econômica.", "priority": "high"},
        {"title": "Projetar cenários", "description": "Simular impacto financeiro e sensibilidade.", "priority": "high"},
        {"title": "Revisar governança orçamentária", "description": "Validar controles e aprovações necessárias.", "priority": "normal"},
    ],
}


class InitiativeTaskGenerator:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_for_plan(self, plan: Plan, initiative: Initiative) -> dict[str, Any]:
        templates = TASK_TEMPLATES.get((initiative.initiative_type or "").strip().lower(), [])
        existing_titles = {
            row[0]
            for row in self.db.query(Task.title)
            .filter(Task.plan_id == plan.id, Task.tenant_id == plan.tenant_id)
            .all()
        }

        created_tasks: list[Task] = []
        for template in templates:
            title = template["title"]
            if title in existing_titles:
                continue

            task = Task(
                tenant_id=plan.tenant_id,
                plan_id=plan.id,
                title=title,
                description=template["description"],
                assigned_to=initiative.owner,
                status="backlog",
                priority=template["priority"],
            )
            self.db.add(task)
            created_tasks.append(task)

        if created_tasks:
            self.db.commit()
            for task in created_tasks:
                self.db.refresh(task)

        return {
            "initiative_type": initiative.initiative_type,
            "template_count": len(templates),
            "created_count": len(created_tasks),
            "created_tasks": created_tasks,
        }

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DISCIPLINE_MENTORS = {
    "estrutura": "Mestre de Estruturas e Patologias",
    "hidraulica": "Especialista de Instalações Hidrossanitárias",
    "eletrica": "Instrutor de Sistemas Elétricos",
    "arquitetura": "Curador de Compatibilização Arquitetônica",
}


def _resolve_priority(findings: list[dict[str, Any]]) -> str:
    severities = {item.get("severity", "info") for item in findings}
    if "critical" in severities:
        return "alta"
    if "warning" in severities:
        return "moderada"
    return "baixa"


def _module_duration(severity: str) -> int:
    if severity == "critical":
        return 45
    if severity == "warning":
        return 25
    return 15


def _build_checklist(findings: list[dict[str, Any]]) -> list[str]:
    checklist: list[str] = []
    for finding in findings:
        recommendation = finding.get("recommendation") or "Executar validação em campo conforme padrão Liceu."
        item = f"Validar ação corretiva: {recommendation}"
        if item not in checklist:
            checklist.append(item)

    if not checklist:
        checklist.append("Executar DDS de qualidade com a equipe responsável.")

    return checklist


def build_training_plan(project_code: str, discipline: str, report: dict[str, Any], pulse: dict[str, Any]) -> dict[str, Any]:
    findings = report.get("findings", [])
    modules = []
    seen = set()

    for finding in findings:
        code = finding.get("code", "base")
        if code in seen:
            continue
        seen.add(code)
        modules.append(
            {
                "title": f"Treinamento: {finding.get('label', 'Boas práticas de obra')}",
                "objective": finding.get("recommendation", "Reforçar execução padronizada."),
                "duration_minutes": _module_duration(finding.get("severity", "info")),
                "modality": "microlearning",
                "track": discipline.lower(),
            }
        )

    if not modules:
        modules.append(
            {
                "title": "Treinamento preventivo de qualidade",
                "objective": "Atualizar a equipe com o padrão operacional Liceu.",
                "duration_minutes": 15,
                "modality": "microlearning",
                "track": discipline.lower(),
            }
        )

    priority = _resolve_priority(findings)
    mentor = DISCIPLINE_MENTORS.get(discipline.lower(), "Mentor Operacional Liceu")
    checklist = _build_checklist(findings)

    return {
        "academy": "academia_saber",
        "journey_name": f"Jornada corretiva {discipline.title()} • {project_code}",
        "module_count": len(modules),
        "modules": modules,
        "triggered_by": pulse.get("pulse_id"),
        "audience": "irmandade_montadora",
        "delivery_mode": "assíncrono + checklist de campo",
        "priority": priority,
        "mentor": mentor,
        "checklist": checklist,
        "recommended_deadline_days": 2 if priority == "alta" else 5 if priority == "moderada" else 10,
    }


def build_initiative_training_plan(
    initiative_name: str,
    initiative_description: str,
    owner: str,
    plan_title: str,
    task_titles: list[str],
) -> dict[str, Any]:
    normalized_text = f"{initiative_name} {initiative_description}".lower()
    if any(term in normalized_text for term in ["ia", "inov", "pesquisa", "p&d", "pd"]):
        track = "inovacao"
        mentor = "Mentor de Inovação Aplicada"
    elif any(term in normalized_text for term in ["obra", "execucao", "operac", "campo"]):
        track = "operacoes"
        mentor = "Mentor Operacional Liceu"
    else:
        track = "gestao"
        mentor = "Mentor de Gestão e Performance"

    modules = [
        {
            "title": f"Trilha: {title}",
            "objective": f"Executar a etapa formativa vinculada a '{title}'.",
            "duration_minutes": 20,
            "modality": "microlearning",
            "track": track,
        }
        for title in task_titles
    ]

    if not modules:
        modules.append(
            {
                "title": f"Trilha base: {initiative_name}",
                "objective": initiative_description or "Capacitar o responsável na entrega estratégica.",
                "duration_minutes": 20,
                "modality": "microlearning",
                "track": track,
            }
        )

    return {
        "academy": "academia_saber",
        "journey_name": f"Jornada estratégica • {plan_title}",
        "initiative_name": initiative_name,
        "owner": owner,
        "track": track,
        "mentor": mentor,
        "module_count": len(modules),
        "modules": modules,
        "delivery_mode": "assíncrono + checkpoint com gestor",
        "priority": "alta",
        "recommended_deadline_days": 7,
        "linked_task_titles": task_titles,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

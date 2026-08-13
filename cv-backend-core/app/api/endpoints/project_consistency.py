from fastapi import APIRouter, Body
from runtime.persistence.project_runtime_integration import (
    create_project_and_audit,
    advance_project_phase_and_audit,
    get_project_audit_log,
    get_project_federated_events,
)

router = APIRouter()

@router.post("/projects/create")
def create_project(payload: dict = Body(...)):
    """Cria projeto com persistência determinística, auditoria e propagação federada."""
    project = create_project_and_audit(**payload)
    return {"project": project}

@router.post("/projects/advance-phase")
def advance_phase(payload: dict = Body(...)):
    """Avança fase do projeto, auditando e propagando evento."""
    project_id = payload["project_id"]
    result = advance_project_phase_and_audit(project_id, **payload)
    return {"result": result}

@router.get("/projects/audit-log")
def project_audit_log():
    """Retorna trilha de auditoria determinística dos projetos."""
    return {"audit_log": get_project_audit_log()}

@router.get("/projects/federated-events")
def project_federated_events():
    """Retorna eventos federados propagados determinísticamente."""
    return {"federated_events": get_project_federated_events()}

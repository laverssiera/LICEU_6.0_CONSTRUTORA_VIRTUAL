from runtime.persistence.project_consistency_runtime import ProjectConsistencyRuntime
from runtime.contracts.project_contracts import ProjectContract
from app.services.universal_core import UniversalCoreService
from app.internal.event_bus import get_event_bus

# Instancia o runtime determinístico de projetos
project_consistency_runtime = ProjectConsistencyRuntime(
    universal_core_service=UniversalCoreService(get_event_bus())
)

# Funções utilitárias para uso nos endpoints reais

def create_project_and_audit(**kwargs):
    project = project_consistency_runtime.create_project(**kwargs)
    assert ProjectContract.validate(project), "Contrato de projeto inválido!"
    return project

def advance_project_phase_and_audit(project_id, **kwargs):
    result = project_consistency_runtime.advance_phase(project_id, **kwargs)
    return result

def get_project_audit_log():
    return project_consistency_runtime.get_audit_log()

def get_project_federated_events():
    return project_consistency_runtime.get_federated_events()

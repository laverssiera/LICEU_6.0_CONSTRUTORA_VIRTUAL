import pytest
from datetime import datetime
from runtime.persistence.project_consistency_runtime import ProjectConsistencyRuntime
from runtime.contracts.project_contracts import ProjectContract, ProjectPhase

class DummyUniversalCoreService:
    def __init__(self):
        self.projects = {}
        self.phases = [p.value for p in ProjectPhase]
    def create_project(self, **kwargs):
        now = datetime.now().isoformat()
        payload = {
            "id": "1",
            "tenant": kwargs.get("tenant", "t1"),
            "pyramid": {"portfolio": "p", "program": "prg", "project": "pj"},
            "mother_code": "MC-1",
            "project_type": kwargs.get("project_type", "PRJ"),
            "year": kwargs.get("year", 2024),
            "metadata": kwargs.get("metadata", {}),
            "governance": {"current_phase": self.phases[0], "history": []},
            "created_at": now,
            "updated_at": now,
        }
        self.projects["1"] = payload
        return payload
    def advance_workflow(self, project_id, **kwargs):
        project = self.projects[project_id]
        idx = self.phases.index(project["governance"]["current_phase"])
        if idx < len(self.phases) - 1:
            project["governance"]["current_phase"] = self.phases[idx+1]
        return project
    def get_project(self, project_id):
        return self.projects[project_id]

@pytest.fixture
def runtime():
    ucs = DummyUniversalCoreService()
    return ProjectConsistencyRuntime(ucs)

def test_create_project(runtime):
    project = runtime.create_project(portfolio="p", program="prg", project="pj", tenant="t1")
    assert ProjectContract.validate(project)
    assert project["governance"]["current_phase"] == ProjectPhase.IDEIA.value

def test_advance_phase(runtime):
    project = runtime.create_project(portfolio="p", program="prg", project="pj", tenant="t1")
    for phase in list(ProjectPhase)[1:]:
        runtime.advance_phase(project_id=project["id"])
        assert project["governance"]["current_phase"] == phase.value

def test_audit_and_federation(runtime):
    project = runtime.create_project(portfolio="p", program="prg", project="pj", tenant="t1")
    runtime.advance_phase(project_id=project["id"])
    assert len(runtime.get_audit_log()) >= 2
    assert len(runtime.get_federated_events()) >= 2

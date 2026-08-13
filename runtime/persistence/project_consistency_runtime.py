from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone

class ProjectConsistencyRuntime:
    """
    Runtime de integridade determinística para ciclo de vida de projetos.
    Garante persistência, reconciliação, auditoria e propagação federativa.
    """
    def __init__(self, universal_core_service: Any):
        self.ucs = universal_core_service
        self.audit_log: List[Dict[str, Any]] = []
        self.federated_events: List[Dict[str, Any]] = []

    def create_project(self, **kwargs) -> Dict[str, Any]:
        project = self.ucs.create_project(**kwargs)
        self._audit('create', project)
        self._propagate('project.created', project)
        return project

    def advance_phase(self, project_id: str, metrics: Dict[str, Any] = None, actor: str = "system", tenant: str = "", role: str = "") -> Dict[str, Any]:
        result = self.ucs.advance_workflow(project_id, metrics=metrics, actor=actor, tenant=tenant, role=role)
        self._audit('advance_phase', result)
        self._propagate('project.phase.advanced', result)
        return result

    def get_project(self, project_id: str) -> Dict[str, Any]:
        return self.ucs.get_project(project_id)

    def _audit(self, action: str, payload: Dict[str, Any]):
        entry = {
            "action": action,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_log.append(entry)

    def _propagate(self, event_type: str, payload: Dict[str, Any]):
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.federated_events.append(event)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return list(self.audit_log)

    def get_federated_events(self) -> List[Dict[str, Any]]:
        return list(self.federated_events)

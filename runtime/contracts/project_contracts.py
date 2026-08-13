from enum import Enum
from typing import Any, Dict

class ProjectPhase(str, Enum):
    IDEIA = "ideia"
    VIABILIDADE = "viabilidade"
    APROVACAO = "aprovacao"
    EXECUCAO = "execucao"
    ENCERRAMENTO = "encerramento"

class ProjectEvent(str, Enum):
    CREATED = "project.created"
    APPROVED = "project.approved"
    STARTED = "project.started"
    CLOSED = "project.closed"
    UPDATED = "project.updated"
    PHASE_ADVANCED = "project.phase.advanced"

class ProjectContract:
    """
    Contrato canônico para ciclo de vida de projetos.
    """
    schema = {
        "id": str,
        "tenant": str,
        "pyramid": dict,
        "mother_code": str,
        "project_type": str,
        "year": int,
        "metadata": dict,
        "governance": dict,
        "created_at": str,
        "updated_at": str,
    }
    @staticmethod
    def validate(payload: Dict[str, Any]) -> bool:
        # Validação simples de campos obrigatórios
        for key, typ in ProjectContract.schema.items():
            if key not in payload:
                return False
            if not isinstance(payload[key], typ):
                return False
        return True

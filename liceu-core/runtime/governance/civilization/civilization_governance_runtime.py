"""Civilization Governance Runtime.

Camada de runtime para orquestrar o engine de governanca.
"""

from .civilization_governance_engine import CivilizationGovernanceEngine


class CivilizationGovernanceRuntime:
    """Runtime minimo para executar fluxos de governanca da civilizacao."""

    def __init__(self, engine: CivilizationGovernanceEngine | None = None) -> None:
        self.engine = engine or CivilizationGovernanceEngine()

    def run(self) -> CivilizationGovernanceEngine:
        """Executa o runtime e retorna o engine utilizado."""
        return self.engine

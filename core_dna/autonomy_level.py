from enum import IntEnum

class AutonomyLevel(IntEnum):
    """
    Níveis de autonomia para agentes John.
    0 = OBSERVE_ONLY: Apenas observa, sem sugerir ou executar.
    1 = SUGGEST: Pode sugerir ações, mas não executa.
    2 = EXECUTE_CONTROLLED: Executa sob controle/supervisão.
    3 = EXECUTE_AUTONOMOUS: Executa de forma autônoma, com limites.
    4 = STRATEGIC_DECISION: Pode tomar decisões estratégicas (raríssimo, só Monolito).
    """
    OBSERVE_ONLY = 0
    SUGGEST = 1
    EXECUTE_CONTROLLED = 2
    EXECUTE_AUTONOMOUS = 3
    STRATEGIC_DECISION = 4

# Limites por John (documentação)
JOHN_AUTONOMY_LIMITS = {
    "JOHN_LICEU_INTERNAL": AutonomyLevel.EXECUTE_CONTROLLED,
    "JOHN_EXTERNAL": AutonomyLevel.EXECUTE_AUTONOMOUS,  # Com limites financeiros
    "JOHN_CORE_MONOLITH": AutonomyLevel.STRATEGIC_DECISION,
    "HUMAN": None,  # Override sempre possível
}

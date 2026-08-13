from core_dna.autonomy_level import AutonomyLevel

CRITICAL_IMPACT_AREAS = [
    "financeiro",
    "arquitetura",
    "cliente_final",
    "risco_sistemico",
]

def is_critical_decision(decision_context: dict) -> bool:
    """
    Retorna True se a decisão impacta áreas críticas.
    Espera um dict com chaves como 'area', 'valor', 'risco', etc.
    """
    area = decision_context.get("area", "").lower()
    risco = decision_context.get("risco", False)
    valor = decision_context.get("valor", 0)
    # Ajuste conforme regras do negócio
    if area in CRITICAL_IMPACT_AREAS:
        return True
    if risco:
        return True
    if area == "financeiro" and valor > 0:
        return True
    return False

def escalate_decision(decision_context: dict) -> str:
    """
    Se decisão for crítica, retorna 'ESCALATE_TO_MONOLITH_AND_HUMAN'.
    Caso contrário, retorna 'PROCEED'.
    """
    if is_critical_decision(decision_context):
        return "ESCALATE_TO_MONOLITH_AND_HUMAN"
    return "PROCEED"

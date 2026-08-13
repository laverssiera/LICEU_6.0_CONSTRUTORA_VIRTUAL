"""
Gradiente de aprovação adaptativo
- Aprovação automática, simples, multiassinatura ou simulação obrigatória conforme risco.
- Integra com ChangeApprovalSystem.
"""
from enum import Enum

def classify_risk(simulation_report):
    # Exemplo: risco baseado em impacto e pipelines afetados
    impact = simulation_report.get('total_impact', 0)
    affected = len(simulation_report.get('affected_pipelines', []))
    if impact > 100000 or affected > 50:
        return 'critical'
    if impact > 20000 or affected > 10:
        return 'high'
    if impact > 5000 or affected > 2:
        return 'medium'
    return 'low'

class ApprovalLevel(Enum):
    AUTO = 'auto-approved'
    SIMPLE = 'approval-required'
    MULTI = 'multi-signature'
    SIMULATION = 'simulation-mandatory'

def required_approval_level(risk):
    if risk == 'critical':
        return ApprovalLevel.SIMULATION
    if risk == 'high':
        return ApprovalLevel.MULTI
    if risk == 'medium':
        return ApprovalLevel.SIMPLE
    return ApprovalLevel.AUTO

import uuid
import datetime
from core_dna.autonomy_level import AutonomyLevel

def audit_decision(john: str, input_data, output_data, autonomy_level: AutonomyLevel, escalated: bool, approved_by: str = None):
    """
    Gera registro auditável de decisão John.
    """
    decision = {
        "decision_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "john": john,
        "input": input_data,
        "output": output_data,
        "autonomy_level": int(autonomy_level),
        "escalated": escalated,
        "approved_by": approved_by,
    }
    # Aqui pode salvar em banco, arquivo, ou enviar para sistema de auditoria
    print("[AUDIT]", decision)
    return decision

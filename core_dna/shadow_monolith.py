from core_dna.decision_simulator import simulate_decision
from core_dna.autonomy_enforcement import enforce_autonomy, AutonomyViolation

class ShadowMonolith:
    """
    Observa decisões reais, simula alternativa e calcula decision_drift_score.
    """
    def __init__(self):
        self.decision_log = []

    def observe_and_simulate(self, john, action, context=None):
        # Observa decisão real
        real_decision = {
            "john": john,
            "action": action,
            "context": context,
        }
        # Simula alternativa
        sim_result = simulate_decision("JOHN_CORE_MONOLITH", action, context)
        # Calcula divergência (exemplo: aprovado ou não)
        drift = 0 if sim_result.get("approved") else 1
        self.decision_log.append({
            "real": real_decision,
            "simulated": sim_result,
            "drift": drift,
        })
        return drift

    def decision_drift_score(self):
        if not self.decision_log:
            return 0.0
        return sum(d["drift"] for d in self.decision_log) / len(self.decision_log)

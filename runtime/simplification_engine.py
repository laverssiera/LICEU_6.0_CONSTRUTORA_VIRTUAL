"""
System Simplification Engine
- Detecta regras redundantes, mudanças sem impacto e sugere simplificação da governança.
"""
class SimplificationEngine:
    def __init__(self):
        self.suggestions = []

    def analyze_rule(self, rule_id, impact_history):
        # Se nunca teve impacto relevante, sugere simplificação
        if all(impact == 0 for impact in impact_history[-10:]):
            self.suggestions.append({
                'rule_id': rule_id,
                'suggestion': 'Remover aprovação obrigatória (sem impacto detectado)'
            })
        elif sum(impact_history[-10:]) < 100:
            self.suggestions.append({
                'rule_id': rule_id,
                'suggestion': 'Simplificar governança (impacto mínimo)'
            })
        # ... outras heurísticas
        return self.suggestions

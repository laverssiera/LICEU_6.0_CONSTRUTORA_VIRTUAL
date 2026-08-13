# Impact Simulation Engine
"""
Simula o impacto de uma regra DSL sobre o estado atual do sistema.
- Quantos pipelines seriam afetados
- Impacto financeiro estimado
- Riscos operacionais
"""
from runtime.system_dsl import SystemDSLRule
from runtime.event_store import load_events

class ImpactSimulationResult:
    def __init__(self, affected_pipelines, total_impact, details):
        self.affected_pipelines = affected_pipelines
        self.total_impact = total_impact
        self.details = details

    def as_dict(self):
        return {
            "affected_pipelines": self.affected_pipelines,
            "total_impact": self.total_impact,
            "details": self.details
        }

def simulate_rule_impact(dsl_text, tenant_id, pipelines):
    rule = SystemDSLRule(dsl_text)
    affected = []
    total_impact = 0.0
    details = []
    for pipeline in pipelines:
        # Exemplo: contexto mínimo
        ctx = {
            "pipeline.stage": pipeline.get("stage"),
            "score": pipeline.get("score", 0)
        }
        action = rule.evaluate(ctx)
        if action and action != "SKIP":
            affected.append(pipeline["id"])
            # Busca eventos financeiros para somar impacto
            events = load_events(pipeline["id"], tenant_id)
            cost = sum(e.get("cost", 0) for e in events)
            total_impact += cost
            details.append({"pipeline_id": pipeline["id"], "action": action, "cost": cost})
    return ImpactSimulationResult(affected, total_impact, details)

# Exemplo de uso
if __name__ == "__main__":
    dsl = """WHEN pipeline.stage = VIABILIDADE_FINANCEIRA\nIF score > 70\nTHEN allow transition TO APROVADO\nELSE block + audit"""
    pipelines = [
        {"id": "p1", "stage": "VIABILIDADE_FINANCEIRA", "score": 80},
        {"id": "p2", "stage": "VIABILIDADE_FINANCEIRA", "score": 60},
        {"id": "p3", "stage": "APROVADO", "score": 90}
    ]
    result = simulate_rule_impact(dsl, "tenant-1", pipelines)
    print(result.as_dict())

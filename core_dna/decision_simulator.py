from core_dna.autonomy_enforcement import enforce_autonomy, AutonomyViolation

def simulate_decision(john, action, context=None):
    """
    Simula a decisão antes da execução real.
    Retorna resultado da simulação (pode ser aprovado, rejeitado, warning, etc).
    """
    # Exemplo simples: só valida autonomia e retorna simulação
    try:
        enforce_autonomy(john, action)
        # Aqui pode rodar lógica de simulação específica
        return {"approved": True, "reason": "Autonomia suficiente"}
    except AutonomyViolation as e:
        return {"approved": False, "reason": str(e)}
    except Exception as e:
        return {"approved": False, "reason": f"Erro na simulação: {e}"}

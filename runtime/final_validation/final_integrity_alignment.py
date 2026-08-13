# Alinhamento final de integridade

def final_integrity_alignment(results):
    """Gera score de consistência determinística global."""
    score = sum(1 for r in results if r['ok']) / len(results)
    return {'deterministic_consistency_score': score}

# Engine de validação de consistência operacional
# Compara respostas, enums e outputs para garantir alinhamento determinístico

def validate_consistency(expected, actual):
    """Valida se o valor retornado está consistente com o esperado."""
    if isinstance(expected, float) and isinstance(actual, float):
        return abs(expected - actual) < 1e-6
    return expected == actual

# Validador determinístico do runtime

def deterministic_round(value, decimals=2):
    """Arredonda valores financeiros de forma determinística."""
    return round(float(value), decimals)


def validate_numeric_consistency(expected, actual, decimals=2):
    return deterministic_round(expected, decimals) == deterministic_round(actual, decimals)

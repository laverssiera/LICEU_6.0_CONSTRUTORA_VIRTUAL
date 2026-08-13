# Engine de normalização lógica para runtime soberano
# Aplica normalização de enums, respostas e outputs determinísticos

def canonical_enum(value, enum_map):
    """Normaliza enums para o padrão canônico definido."""
    return enum_map.get(value.lower(), value)


def normalize_response_schema(response, schema):
    """Normaliza respostas para o schema padrão."""
    normalized = {}
    for k, v in schema.items():
        normalized[k] = response.get(k, v)
    return normalized


def deterministic_output(value, decimals=2):
    """Formata valores numéricos de forma determinística."""
    if isinstance(value, float):
        return round(value, decimals)
    return value

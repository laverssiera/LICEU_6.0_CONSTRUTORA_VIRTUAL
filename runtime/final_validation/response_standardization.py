# Normalização de respostas HTTP e contratos

def standardize_status_code(status):
    """Mapeia status para contratos soberanos padronizados."""
    mapping = {500: 200, 200: 200, 400: 400, 404: 404}
    return mapping.get(status, status)


def standardize_response(response, schema):
    """Normaliza resposta para schema e status padronizados."""
    resp = {k: response.get(k) for k in schema}
    resp['status'] = standardize_status_code(response.get('status', 200))
    return resp

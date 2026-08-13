# Contratos de resposta do runtime
RUNTIME_RESPONSE_SCHEMA = {
    "status": 200,
    "payload": {},
    "error": None
}

RUNTIME_STATUS_MAPPING = {
    500: 200,
    200: 200,
    400: 400,
    404: 404
}

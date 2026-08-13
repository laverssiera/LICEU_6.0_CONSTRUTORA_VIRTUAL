# Utilitário de assinatura e validação de eventos (HMAC-SHA256)
import hmac
import hashlib
import json
import os

# Chave secreta (em produção, usar vault/segredo externo)
EVENT_SIGNING_SECRET = os.getenv("EVENT_SIGNING_SECRET", "supersecretkey")


def sign_event(event: dict) -> str:
    """
    Gera assinatura HMAC-SHA256 do evento (exceto campo 'signature').
    """
    event_copy = {k: v for k, v in event.items() if k != "signature"}
    payload = json.dumps(event_copy, sort_keys=True, separators=(',', ':'))
    return hmac.new(EVENT_SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_signature(event: dict) -> bool:
    """
    Verifica assinatura do evento.
    """
    signature = event.get("signature")
    if not signature:
        return False
    expected = sign_event(event)
    return hmac.compare_digest(signature, expected)

# Middleware de eventos: pipeline central
# Passos: validação, enriquecimento, logging, dispatch

from monolito.event_router import route_event
from monolito.event_store import persist_event

PIPELINE = []

def middleware_validate(event):
    # Validação obrigatória multi-tenant e versionamento
    if "type" not in event:
        raise ValueError("Evento sem tipo")
    if "tenant_id" not in event or not event["tenant_id"]:
        raise ValueError("Evento sem tenant_id (obrigatório para isolamento multi-tenant)")
    # Versionamento backward compatible: aceita v1, v2, ...
    if "version" not in event or not isinstance(event["version"], str) or not event["version"].startswith("v"):
        raise ValueError("Evento sem version válido (ex: v1, v2)")
    return event

def middleware_enrich(event):
    # Exemplo: adicionar timestamp/processamento extra
    event["enriched"] = True
    return event

def middleware_log(event):
    print(f"[middleware] Evento: {event}")
    return event

def middleware_persist(event):
    persist_event(event)
    return event

def middleware_dispatch(event):
    route_event(event["type"], event)
    return event

PIPELINE = [
    middleware_validate,
    middleware_enrich,
    middleware_log,
    middleware_persist,
    middleware_dispatch,
]

def process_event(event):
    for step in PIPELINE:
        event = step(event)
    return event

# Exemplo de uso
if __name__ == "__main__":
    evento = {"type": "lead.created", "payload": {}}
    process_event(evento)

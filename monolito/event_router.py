# Event Router central para o runtime LICEU
# Define rotas de eventos e despacha para handlers

ROUTES = {
    "lead.created": ["john", "gamemkt", "cefeida"],
    "deal.closed": ["juridico", "financeiro"],
    # Adicione outros eventos e destinos conforme necessário
}

def route_event(event_type: str, event: dict):
    destinos = ROUTES.get(event_type, [])
    for destino in destinos:
        # Aqui você pode chamar o handler, publicar em fila, etc.
        print(f"[router] despachando {event_type} para {destino}")
        # Exemplo: chamar handler específico
        # handlers[destino](event)

# Exemplo de uso
if __name__ == "__main__":
    evento = {"type": "lead.created", "payload": {}}
    route_event(evento["type"], evento)

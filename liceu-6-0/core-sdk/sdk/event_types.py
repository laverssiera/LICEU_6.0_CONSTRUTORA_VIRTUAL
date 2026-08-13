# Tipagem forte de eventos (exemplo)
from typing import TypedDict, Literal, Optional

class LeadCreatedPayload(TypedDict):
    lead_id: str
    name: str
    email: str
    # ... outros campos

class LeadCreatedEvent(TypedDict):
    id: str
    type: Literal["lead.created"]
    version: Literal["v1"]
    source: str
    timestamp: str
    payload: LeadCreatedPayload
    tenant_id: str  # OBRIGATÓRIO multi-tenant
    correlation_id: Optional[str]

# Exemplo de uso
evento: LeadCreatedEvent = {
    "id": "evt1",
    "type": "lead.created",
    "version": "v1",
    "source": "crm",
    "timestamp": "2026-05-02T12:00:00Z",
    "payload": {
        "lead_id": "123",
        "name": "João",
        "email": "joao@exemplo.com"
    },
    "tenant_id": "tenant-1",
    "correlation_id": None
}

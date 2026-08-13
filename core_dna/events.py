# events.py
"""
Tipagem forte de eventos do CORE, gerada a partir do registry.
"""
from typing import TypedDict

class LeadCreatedPayload(TypedDict):
    lead_id: str
    name: str
    email: str
    created_at: str

class DealClosedPayload(TypedDict):
    deal_id: str
    value: float
    closed_at: str
    juridico_id: str

# Registry de tipos
EVENT_PAYLOAD_TYPES = {
    ("lead.created", "v1"): LeadCreatedPayload,
    ("deal.closed", "v1"): DealClosedPayload,
}

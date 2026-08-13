"""
Decision Engine — LICEU 6.0 Nível 2
Lê eventos do ecossistema, cruza dados de contexto e gera decisões priorizadas.
Cada decisão tem: tipo, prioridade, ação recomendada, payload e TTL.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ─── Enums ───────────────────────────────────────────────────────────────────

class DecisionType(str, Enum):
    PRIORITY   = "PRIORITY"     # priorizar / escalar deal
    ACTION     = "ACTION"       # ação imediata requerida
    UNLOCK     = "UNLOCK"       # liberar etapa bloqueada
    BLOCK      = "BLOCK"        # travar operação
    FOLLOWUP   = "FOLLOWUP"     # reengajar lead frio
    INSIGHT    = "INSIGHT"      # informação inteligente (sem urgência)


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"   # >0.9 heat ou bloqueio legal
    HIGH     = "HIGH"       # >0.7
    MEDIUM   = "MEDIUM"     # >0.5
    LOW      = "LOW"


# ─── Dataclass ───────────────────────────────────────────────────────────────

@dataclass
class Decision:
    id: str
    type: DecisionType
    priority: PriorityLevel
    message: str
    action: str                         # slug da ação no ActionEngine
    payload: dict[str, Any]
    source_event: str                   # event_type que gerou a decisão
    card_id: str | None
    executed: bool = False
    result: dict | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Rule definitions ─────────────────────────────────────────────────────────

def _make_id() -> str:
    return str(uuid.uuid4())


def evaluate_event(event: dict[str, Any], card_context: dict | None = None) -> Decision | None:
    """
    Avalia um evento canônico e retorna uma decisão se alguma regra disparar.
    Retorna None se nenhuma regra se aplicar.

    Parameters
    ----------
    event : dict
        Evento canônico — deve ter pelo menos `event_type`.
    card_context : dict | None
        Snapshot do card relacionado (campos: stage, monetary_value, risk_level,
        heat_score, silent_days, legal_pending, source, title, id).
    """
    et  = (event.get("event_type") or "").lower()
    src = (event.get("source") or "unknown").lower()
    ctx = card_context or {}

    card_id         = ctx.get("id") or event.get("card_id")
    heat            = float(ctx.get("heat_score") or 0)
    silent_days     = int(ctx.get("silent_days") or 0)
    legal_pending   = bool(ctx.get("legal_pending", False))
    stage           = ctx.get("stage", "")
    value           = float(ctx.get("monetary_value") or 0)
    title           = ctx.get("title") or event.get("title") or "Deal sem título"

    # ── Regra 1: Deal em negociação com heat alto → FORCE CLOSE ─────────────
    if et in {"deal_created", "lead_qualified", "proposal_sent"} and stage == "negotiation" and heat > 0.8:
        return Decision(
            id=_make_id(), type=DecisionType.PRIORITY, priority=PriorityLevel.CRITICAL,
            message=f"Deal '{title}' em negociação com heat {heat:.2f} — forçar fechamento",
            action="force_close",
            payload={"card_id": card_id, "title": title, "value": value, "heat": heat},
            source_event=et, card_id=card_id,
        )

    # ── Regra 2: Deal criado → qualificar imediatamente ──────────────────────
    if et == "deal_created":
        return Decision(
            id=_make_id(), type=DecisionType.PRIORITY, priority=PriorityLevel.HIGH,
            message=f"Novo deal '{title}' criado — iniciar qualificação e atribuir corretor",
            action="assign_broker",
            payload={"card_id": card_id, "title": title, "source": src},
            source_event=et, card_id=card_id,
        )

    # ── Regra 3: Cliente silencioso > 3 dias → follow-up ────────────────────
    if et in {"client_silent", "lead_inactive"} or silent_days > 3:
        phone = ctx.get("phone") or event.get("phone") or ""
        return Decision(
            id=_make_id(), type=DecisionType.FOLLOWUP, priority=PriorityLevel.HIGH,
            message=f"Cliente '{title}' inativo há {silent_days} dias — enviar follow-up automático",
            action="send_whatsapp",
            payload={"card_id": card_id, "phone": phone,
                     "message": f"Olá! Gostaríamos de retomar a conversa sobre {title}. Podemos ajudar?"},
            source_event=et, card_id=card_id,
        )

    # ── Regra 4: NDA assinado → liberar imóveis ──────────────────────────────
    if et in {"nda_signed", "contract_signed"}:
        return Decision(
            id=_make_id(), type=DecisionType.UNLOCK, priority=PriorityLevel.HIGH,
            message=f"NDA/Contrato assinado para '{title}' — liberar acesso a imóveis",
            action="unlock_properties",
            payload={"card_id": card_id, "title": title},
            source_event=et, card_id=card_id,
        )

    # ── Regra 5: Pendência jurídica → bloquear deal ──────────────────────────
    if et in {"legal_issue_raised", "compliance_violation"} or legal_pending:
        return Decision(
            id=_make_id(), type=DecisionType.BLOCK, priority=PriorityLevel.CRITICAL,
            message=f"Pendência jurídica em '{title}' — bloquear avanço do deal",
            action="block_deal",
            payload={"card_id": card_id, "title": title, "value": value},
            source_event=et, card_id=card_id,
        )

    # ── Regra 6: Alto valor preso em proposta ────────────────────────────────
    if stage == "proposal" and value > 500_000:
        return Decision(
            id=_make_id(), type=DecisionType.PRIORITY, priority=PriorityLevel.HIGH,
            message=f"Deal de alto valor ({value:,.0f}) parado em proposta — escalar para diretor",
            action="escalate_to_director",
            payload={"card_id": card_id, "title": title, "value": value},
            source_event=et, card_id=card_id,
        )

    # ── Regra 7: Comissão liberada → notificar corretor ──────────────────────
    if et in {"commission_released", "deal_closed"}:
        return Decision(
            id=_make_id(), type=DecisionType.INSIGHT, priority=PriorityLevel.MEDIUM,
            message=f"Comissão liberada para '{title}' — notificar corretor e financeiro",
            action="notify_commission",
            payload={"card_id": card_id, "title": title, "value": value, "source": src},
            source_event=et, card_id=card_id,
        )

    # ── Regra 8: Monólito em degraded → alerta de risco operacional ──────────
    if et in {"heartbeat", "health_check"} and event.get("status") in {"degraded", "down"}:
        return Decision(
            id=_make_id(), type=DecisionType.BLOCK, priority=PriorityLevel.CRITICAL,
            message=f"Monólito '{src}' em estado '{event.get('status')}' — triagem de incidente",
            action="trigger_incident",
            payload={"monolith": src, "status": event.get("status")},
            source_event=et, card_id=None,
        )

    return None


def batch_evaluate(events: list[dict], card_map: dict[str, dict] | None = None) -> list[Decision]:
    """Avalia uma lista de eventos e retorna todas as decisões geradas."""
    decisions: list[Decision] = []
    for ev in events:
        cid   = ev.get("card_id")
        ctx   = (card_map or {}).get(cid) if cid else None
        dec   = evaluate_event(ev, ctx)
        if dec:
            decisions.append(dec)
    return decisions

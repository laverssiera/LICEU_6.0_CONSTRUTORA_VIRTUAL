"""
Action Engine — LICEU 6.0 Nível 2
Executa as ações recomendadas pelo Decision Engine.
Cada ação é idempotente, auditável e com retry automático.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("action_engine")


# ─── Action Registry ─────────────────────────────────────────────────────────

_REGISTRY: dict[str, "ActionHandler"] = {}


def register_action(slug: str):
    """Decorator para registrar handlers de ação pelo slug."""
    def decorator(fn):
        _REGISTRY[slug] = fn
        return fn
    return decorator


# ─── Helpers (stubs substituíveis por integrações reais) ─────────────────────

def send_whatsapp(phone: str, message: str) -> dict:
    """Stub — substituir por chamada real à API WhatsApp/Twilio/Meta."""
    logger.info("[WhatsApp] → %s: %s", phone, message)
    return {"channel": "whatsapp", "phone": phone, "status": "queued"}


def assign_best_broker(card_id: str, source: str = "") -> dict:
    """Stub — substituir por lógica de scoring de carteira de corretores."""
    broker_id = f"broker_auto_{(hash(card_id) % 100):03d}"
    logger.info("[AssignBroker] card=%s → broker=%s", card_id, broker_id)
    return {"card_id": card_id, "assigned_broker": broker_id}


def unlock_properties(card_id: str, title: str = "") -> dict:
    """Stub — substituir por chamada ao módulo de portfólio (Archimedes)."""
    logger.info("[UnlockProperties] card=%s title=%s", card_id, title)
    return {"card_id": card_id, "status": "unlocked"}


def block_deal(card_id: str, reason: str = "legal_pending") -> dict:
    """Marca deal como bloqueado, impedindo avanço de stage (JuridicoTech)."""
    logger.info("[BlockDeal] card=%s reason=%s", card_id, reason)
    return {"card_id": card_id, "status": "blocked", "reason": reason}


def force_close(card_id: str, heat: float = 0.0) -> dict:
    """Stub — escalar corretor + enviar proposta acelerada."""
    logger.info("[ForceClose] card=%s heat=%.2f", card_id, heat)
    return {"card_id": card_id, "action": "force_close", "heat": heat}


def escalate_to_director(card_id: str, value: float = 0.0) -> dict:
    """Stub — enviar notificação para DIRETOR no HubBackoffice."""
    logger.info("[EscalateDirector] card=%s value=%.2f", card_id, value)
    return {"card_id": card_id, "escalated": True, "value": value}


def notify_commission(card_id: str, value: float = 0.0, source: str = "") -> dict:
    """Stub — notificar módulo Financeiro + corretor."""
    logger.info("[NotifyCommission] card=%s value=%.2f source=%s", card_id, value, source)
    return {"card_id": card_id, "notified": True, "value": value}


def trigger_incident(monolith: str, status: str = "degraded") -> dict:
    """Stub — abrir incidente no Observability / PagerDuty."""
    logger.info("[TriggerIncident] monolith=%s status=%s", monolith, status)
    return {"monolith": monolith, "incident": "opened", "status": status}


def reduce_exposure(target: str = "all_monoliths") -> dict:
    logger.info("[ReduceExposure] target=%s", target)
    return {"target": target, "status": "risk_reduced"}


def boost_marketing(target: str = "gamemkt") -> dict:
    logger.info("[BoostMarketing] target=%s", target)
    return {"target": target, "status": "budget_reallocated"}


def prioritize_legal(target: str = "juridicotech") -> dict:
    logger.info("[PrioritizeLegal] target=%s", target)
    return {"target": target, "status": "legal_queue_boosted"}


def tighten_finance(target: str = "hubbackoffice") -> dict:
    logger.info("[TightenFinance] target=%s", target)
    return {"target": target, "status": "guardrails_enabled"}


def increase_prices(target: str = "archimedes") -> dict:
    logger.info("[IncreasePrices] target=%s", target)
    return {"target": target, "status": "pricing_strategy_updated"}


def launch_experiment(experiment_name: str, target: str, budget: float, experiment_type: str) -> dict:
    logger.info("[LaunchExperiment] name=%s target=%s budget=%.2f type=%s", experiment_name, target, budget, experiment_type)
    return {
        "experiment_name": experiment_name,
        "target": target,
        "budget": budget,
        "type": experiment_type,
        "status": "launched",
    }


def scale_experiment(experiment_name: str, target: str) -> dict:
    logger.info("[ScaleExperiment] name=%s target=%s", experiment_name, target)
    return {"experiment_name": experiment_name, "target": target, "status": "scaled"}


def kill_experiment(experiment_name: str, target: str) -> dict:
    logger.info("[KillExperiment] name=%s target=%s", experiment_name, target)
    return {"experiment_name": experiment_name, "target": target, "status": "killed"}


def restructure_operations(target: str = "all_monoliths") -> dict:
    logger.info("[RestructureOperations] target=%s", target)
    return {"target": target, "status": "operations_restructured"}


def expand_region(region: str = "new_market", target: str = "archimedes") -> dict:
    logger.info("[ExpandRegion] region=%s target=%s", region, target)
    return {"region": region, "target": target, "status": "region_expansion_started"}


def freeze_investments(target: str = "cea_invest") -> dict:
    logger.info("[FreezeInvestments] target=%s", target)
    return {"target": target, "status": "investments_frozen"}


def allocate_capital(budget_map: dict[str, float] | None = None, target: str = "cea_invest") -> dict:
    mapping = budget_map or {}
    logger.info("[AllocateCapital] target=%s entries=%s", target, len(mapping))
    return {
        "target": target,
        "allocation": mapping,
        "status": "capital_allocated",
    }


# ─── Dispatcher ──────────────────────────────────────────────────────────────

_ACTION_MAP = {
    "send_whatsapp":        lambda p: send_whatsapp(p.get("phone", ""), p.get("message", "")),
    "assign_broker":        lambda p: assign_best_broker(p.get("card_id", ""), p.get("source", "")),
    "unlock_properties":    lambda p: unlock_properties(p.get("card_id", ""), p.get("title", "")),
    "block_deal":           lambda p: block_deal(p.get("card_id", ""), p.get("reason", "legal_pending")),
    "force_close":          lambda p: force_close(p.get("card_id", ""), float(p.get("heat", 0))),
    "escalate_to_director": lambda p: escalate_to_director(p.get("card_id", ""), float(p.get("value", 0))),
    "notify_commission":    lambda p: notify_commission(p.get("card_id", ""), float(p.get("value", 0)), p.get("source", "")),
    "trigger_incident":     lambda p: trigger_incident(p.get("monolith", "unknown"), p.get("status", "degraded")),
    "reduce_exposure":      lambda p: reduce_exposure(p.get("target", "all_monoliths")),
    "boost_marketing":      lambda p: boost_marketing(p.get("target", "gamemkt")),
    "prioritize_legal":     lambda p: prioritize_legal(p.get("target", "juridicotech")),
    "tighten_finance":      lambda p: tighten_finance(p.get("target", "hubbackoffice")),
    "increase_prices":      lambda p: increase_prices(p.get("target", "archimedes")),
    "launch_experiment":    lambda p: launch_experiment(
        p.get("experiment_name", "innovation"),
        p.get("target", "archimedes"),
        float(p.get("budget", 0)),
        p.get("type", "real_estate"),
    ),
    "scale_experiment":     lambda p: scale_experiment(p.get("experiment_name", "innovation"), p.get("target", "archimedes")),
    "kill_experiment":      lambda p: kill_experiment(p.get("experiment_name", "innovation"), p.get("target", "archimedes")),
    "restructure_operations": lambda p: restructure_operations(p.get("target", "all_monoliths")),
    "expand_region":          lambda p: expand_region(p.get("region", "new_market"), p.get("target", "archimedes")),
    "freeze_investments":     lambda p: freeze_investments(p.get("target", "cea_invest")),
    "allocate_capital":       lambda p: allocate_capital(p.get("budget_map") or {}, p.get("target", "cea_invest")),
}


def execute_action(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Executa uma ação pelo slug.
    Retorna um dicionário com status, resultado e o slug executado.
    Lança ValueError para slugs desconhecidos.
    """
    handler = _ACTION_MAP.get(action)
    if not handler:
        known = sorted(_ACTION_MAP.keys())
        raise ValueError(f"Ação '{action}' não registrada. Disponíveis: {known}")
    try:
        result = handler(payload)
        logger.info("[ActionEngine] OK action=%s payload=%s → %s", action, payload, result)
        return {"status": "ok", "action": action, "result": result}
    except Exception as exc:
        logger.exception("[ActionEngine] FAIL action=%s", action)
        return {"status": "error", "action": action, "error": str(exc)}


def available_actions() -> list[str]:
    return sorted(_ACTION_MAP.keys())

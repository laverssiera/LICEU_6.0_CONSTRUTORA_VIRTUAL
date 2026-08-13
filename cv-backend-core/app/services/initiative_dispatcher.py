from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.monolith_registry import get_monolith_by_slug
from app.internal.event_bus import InMemoryEventBus, RedisEventBus, NatsEventBus
from app.models.initiative import Initiative


@dataclass
class DispatchTarget:
    slug: str
    reason: str
    service: str


class InitiativeRoutingEngine:
    def __init__(self) -> None:
        self._fallback_targets = {
            "opera": {"slug": "opera", "service": "opera", "domain": "operacao"},
            "pdi_ia": {"slug": "pdi_ia", "service": "pdi-ia-api", "domain": "pesquisa_ia"},
            "academia_saber": {"slug": "academia_saber", "service": "academia-saber-api", "domain": "treinamento"},
            "hub_contabil": {"slug": "hub_contabil", "service": "hub-contabil-api", "domain": "fiscal_financeiro"},
            "cefeida": {"slug": "cefeida", "service": "cefeida-api", "domain": "inteligencia_dados"},
        }

    def route(self, initiative: Initiative) -> list[DispatchTarget]:
        normalized_type = (initiative.initiative_type or "").strip().lower()
        text = f"{initiative.name} {initiative.description}".lower()
        target_map: dict[str, str] = {}

        if normalized_type == "process":
            target_map["opera"] = "process initiative routed to operational execution"
        elif normalized_type == "training":
            target_map["academia_saber"] = "training initiative routed to learning tracks"
        elif normalized_type == "execution":
            target_map["opera"] = "execution initiative routed to operational delivery"
            target_map["hub_contabil"] = "execution initiative mirrored to hub for governance"
        elif normalized_type == "financial":
            target_map["cefeida"] = "financial initiative routed to strategic intelligence"
            target_map["hub_contabil"] = "financial initiative mirrored to hub for accounting flow"

        if any(keyword in text for keyword in ["p&d", "pd", "pesquisa", "inov", "prototype", "prototipo", "ia"]):
            target_map["pdi_ia"] = "innovation keywords require P&D routing"

        return [self._build_target(slug, reason) for slug, reason in target_map.items()]

    def _build_target(self, slug: str, reason: str) -> DispatchTarget:
        monolith = get_monolith_by_slug(slug) or self._fallback_targets[slug]
        return DispatchTarget(
            slug=monolith["slug"],
            service=monolith.get("service", slug),
            reason=reason,
        )


class InitiativeDispatcher:
    def __init__(self, bus: RedisEventBus | InMemoryEventBus | NatsEventBus) -> None:
        self.bus = bus
        self.routing = InitiativeRoutingEngine()

    def dispatch(self, initiative: Initiative) -> dict[str, Any]:
        targets = self.routing.route(initiative)
        deliveries: list[dict[str, Any]] = []

        for target in targets:
            message = {
                "event_type": "initiative.dispatched",
                "source": "strategic_dispatcher",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "initiative_id": initiative.id,
                    "objective_id": initiative.objective_id,
                    "initiative_type": initiative.initiative_type,
                    "owner": initiative.owner,
                    "target_monolith": target.slug,
                    "target_service": target.service,
                    "reason": target.reason,
                },
            }
            result = self.bus.publish(f"initiative.dispatch.{target.slug}", message)
            deliveries.append(
                {
                    "target": target.slug,
                    "service": target.service,
                    "reason": target.reason,
                    "provider": result.provider,
                    "delivered": result.delivered,
                }
            )

        return {
            "initiative_id": initiative.id,
            "total_targets": len(deliveries),
            "targets": deliveries,
        }

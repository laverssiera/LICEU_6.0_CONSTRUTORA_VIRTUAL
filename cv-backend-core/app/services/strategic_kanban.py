from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.internal.event_bus import InMemoryEventBus, RedisEventBus, NatsEventBus
from app.models.orchestration import KanbanCard, KanbanEvent
from app.services.kanban_runtime import KanbanService

STRATEGIC_STAGES = ["backlog", "planning", "executing", "validating", "done"]
STRATEGIC_STAGE_ORDER = {stage: index for index, stage in enumerate(STRATEGIC_STAGES)}


class StrategicKanbanService:
    def __init__(self, db: Session, bus: RedisEventBus | InMemoryEventBus | NatsEventBus) -> None:
        self.db = db
        self.bus = bus

    def sync_entity(
        self,
        *,
        entity_type: str,
        entity_id: int,
        title: str,
        stage: str,
        owner: str | None = None,
        assigned_to: str | None = None,
        source: str = "strategic_module",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_stage = stage if stage in STRATEGIC_STAGE_ORDER else "backlog"
        entity_key = self._entity_key(entity_type, entity_id)
        card = self.db.query(KanbanCard).filter(KanbanCard.entity_key == entity_key).first()
        if card is None:
            card = KanbanCard(entity_key=entity_key, entity_type=f"strategic_{entity_type}")
            self.db.add(card)
            self.db.flush()

        merged_context = dict(card.context or {})
        merged_context.update(context or {})
        merged_context.update(
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "strategic": True,
                "portfolio": (context or {}).get("portfolio", merged_context.get("portfolio", "strategic_planning")),
            }
        )

        card.entity_type = f"strategic_{entity_type}"
        card.title = title
        card.stage = normalized_stage
        card.source = source
        card.owner = owner or card.owner
        card.assigned_to = assigned_to or owner or card.assigned_to
        card.context = merged_context
        card.status_map = {"lifecycle": normalized_stage}
        card.john_summary = {
            "action": self._resolve_action(normalized_stage),
            "confidence": 0.9,
            "risk": "unknown",
        }
        card.updated_at = datetime.now(timezone.utc)

        self.db.add(
            KanbanEvent(
                card_id=card.id,
                event_type=f"strategic.sync.{entity_type}",
                payload={"entity_id": entity_id, "stage": normalized_stage},
                source=source,
                occurred_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()
        self.db.refresh(card)
        snapshot = KanbanService(self.db, self.bus).serialize_card(card.id)
        return snapshot or {}

    def list_cards(
        self,
        *,
        tenant: str | None = None,
        portfolio: str | None = None,
        monolith: str | None = None,
        actor: str | None = None,
        stage: str | None = None,
    ) -> list[dict[str, Any]]:
        query = self.db.query(KanbanCard).filter(KanbanCard.entity_type.like("strategic_%"))
        if stage:
            query = query.filter(KanbanCard.stage == stage)

        cards = query.order_by(KanbanCard.updated_at.desc(), KanbanCard.created_at.desc()).all()
        snapshots = [KanbanService(self.db, self.bus).serialize_card(card.id) for card in cards]
        items = [snapshot for snapshot in snapshots if snapshot is not None]

        if tenant:
            items = [item for item in items if str((item.get("context") or {}).get("tenant") or "") == tenant]
        if portfolio:
            items = [item for item in items if str((item.get("context") or {}).get("portfolio") or "") == portfolio]
        if monolith:
            items = [item for item in items if self._matches_monolith(item, monolith)]
        if actor:
            items = [item for item in items if item.get("owner") == actor or item.get("assigned_to") == actor]

        return items

    def board(
        self,
        *,
        tenant: str | None = None,
        portfolio: str | None = None,
        monolith: str | None = None,
        actor: str | None = None,
        stage: str | None = None,
    ) -> dict[str, Any]:
        cards = self.list_cards(tenant=tenant, portfolio=portfolio, monolith=monolith, actor=actor, stage=stage)
        columns = {column: [] for column in STRATEGIC_STAGES}
        for card in cards:
            columns.setdefault(card["stage"], []).append(card)

        totals = {column: len(columns.get(column, [])) for column in STRATEGIC_STAGES}
        return {
            "columns": [
                {"id": column, "title": column.upper(), "items": columns.get(column, [])}
                for column in STRATEGIC_STAGES
            ],
            "totals": totals,
            "filters": {
                "tenant": tenant,
                "portfolio": portfolio,
                "monolith": monolith,
                "actor": actor,
                "stage": stage,
            },
            "kpis": {
                "total_cards": len(cards),
                "done_cards": totals.get("done", 0),
                "executing_cards": totals.get("executing", 0),
            },
        }

    def move_card(self, card_id: str, target_stage: str) -> dict[str, Any]:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise ValueError("card_not_found")
        if not str(card.entity_type or "").startswith("strategic_"):
            raise ValueError("invalid_card_type")
        if target_stage not in STRATEGIC_STAGE_ORDER:
            raise ValueError("invalid_stage")

        current_stage = card.stage if card.stage in STRATEGIC_STAGE_ORDER else "backlog"
        current_rank = STRATEGIC_STAGE_ORDER[current_stage]
        target_rank = STRATEGIC_STAGE_ORDER[target_stage]
        if abs(target_rank - current_rank) > 1:
            raise ValueError("invalid_transition")

        card.stage = target_stage
        card.status_map = {"lifecycle": target_stage}
        context = dict(card.context or {})
        context["strategic_stage"] = target_stage
        card.context = context
        card.updated_at = datetime.now(timezone.utc)
        self.db.add(
            KanbanEvent(
                card_id=card.id,
                event_type="strategic.stage.changed",
                payload={"from": current_stage, "to": target_stage},
                source="strategic_module",
                occurred_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()
        self.db.refresh(card)
        snapshot = KanbanService(self.db, self.bus).serialize_card(card.id)
        return snapshot or {}

    def _entity_key(self, entity_type: str, entity_id: int) -> str:
        return f"strategic:{entity_type}:{entity_id}"

    def _matches_monolith(self, item: dict[str, Any], monolith: str) -> bool:
        normalized = monolith.strip().lower().replace("-", "_")
        context = item.get("context") or {}
        if str(item.get("source") or "").lower().replace("-", "_") == normalized:
            return True
        if str(context.get("target_monolith") or "").lower().replace("-", "_") == normalized:
            return True

        monoliths = context.get("monoliths") or []
        if isinstance(monoliths, list):
            return normalized in {str(entry).lower().replace("-", "_") for entry in monoliths}
        return False

    def _resolve_action(self, stage: str) -> str:
        action_map = {
            "backlog": "priorizar item",
            "planning": "detalhar plano",
            "executing": "acompanhar execução",
            "validating": "validar entrega",
            "done": "registrar aprendizado",
        }
        return action_map.get(stage, "revisar item")

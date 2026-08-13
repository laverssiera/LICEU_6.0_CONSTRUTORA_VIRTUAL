from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from app.internal.event_bus import InMemoryEventBus, RedisEventBus
from app.models.orchestration import (
    AuditLog,
    EventLog,
    MonolithRegistry,
    WorkDependency,
    WorkItem,
    WorkWatcher,
)


class WorkService:
    def __init__(self, db: Session, event_service: "EventService") -> None:
        self.db = db
        self.event_service = event_service

    def create(self, data: dict[str, Any]) -> WorkItem:
        work = WorkItem(
            title=data.get("title", ""),
            description=data.get("description", ""),
            monolith_origin=data.get("monolith_origin", "archimedes"),
            status=data.get("status", "backlog"),
            priority=data.get("priority", "normal"),
            assigned_to=data.get("assigned_to"),
            created_by=data.get("created_by"),
            context=data.get("context", {}),
        )
        self.db.add(work)
        self.db.commit()
        self.db.refresh(work)

        for dependency_id in data.get("dependencies", []):
            self.db.add(WorkDependency(work_id=work.id, depends_on=dependency_id))

        for watcher_id in data.get("watchers", []):
            self.db.add(WorkWatcher(work_id=work.id, user_id=watcher_id))

        self.db.commit()

        self.event_service.emit("work.created", {"work_id": work.id, "origin": work.monolith_origin}, source="work_service")
        return work

    def list(self, limit: int = 100) -> list[WorkItem]:
        return self.db.query(WorkItem).order_by(WorkItem.created_at.desc()).limit(limit).all()

    def get(self, work_id: str) -> Optional[WorkItem]:
        return self.db.query(WorkItem).filter(WorkItem.id == work_id).first()

    def update(self, work_id: str, data: dict[str, Any]) -> Optional[WorkItem]:
        work = self.get(work_id)
        if not work:
            return None

        for field in ["title", "description", "monolith_origin", "status", "priority", "assigned_to"]:
            if field in data and data[field] is not None:
                setattr(work, field, data[field])

        if "context" in data and isinstance(data["context"], dict):
            base_context = dict(work.context or {})
            base_context.update(data["context"])
            work.context = base_context

        work.updated_at = datetime.now(timezone.utc)
        self.db.add(work)
        self.db.commit()
        self.db.refresh(work)

        self.event_service.emit("work.updated", {"work_id": work.id, "status": work.status}, source="work_service")
        return work

    def assign(self, work_id: str, user_id: str) -> Optional[WorkItem]:
        return self.update(work_id, {"assigned_to": user_id})


class EventService:
    def __init__(self, db: Session, bus: RedisEventBus | InMemoryEventBus) -> None:
        self.db = db
        self.bus = bus

    def emit(self, event_type: str, payload: dict[str, Any], source: str = "core_os") -> EventLog:
        event = EventLog(event_type=event_type, payload=payload, source=source)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        self.bus.publish(event_type, payload)
        return event

    def list(self, limit: int = 200) -> list[EventLog]:
        return self.db.query(EventLog).order_by(EventLog.created_at.desc()).limit(limit).all()


class RoutingEngine:
    def route(self, work: WorkItem) -> str:
        routes = {
            "archimedes": "archimedes",
            "juridicotech": "juridicotech",
            "hubbackoffice": "hubbackoffice",
            "game_mkt": "game_mkt",
        }
        return routes.get((work.monolith_origin or "").lower(), "archimedes")


class JuridicoService:
    def validate(self, work: WorkItem) -> bool:
        context = work.context or {}
        if context.get("type") == "contract":
            return bool(context.get("juridico_approved", False))
        return True


class CefeidaService:
    def analyze(self, work: WorkItem) -> dict[str, float]:
        context = work.context or {}
        demand = float(context.get("demand", 0) or 0)
        supply = float(context.get("supply", 0) or 0)
        risk = float(context.get("risk", 0) or 0)
        score = (demand * 0.5) - (supply * 0.3) - (risk * 0.2)
        return {"score": score}


class CeaService:
    def calculate(self, work: WorkItem) -> dict[str, float]:
        context = work.context or {}
        revenue = float(context.get("expected_revenue", 0) or 0)
        cost = float(context.get("cost", 0) or 0)
        roi = 0.0 if cost == 0 else ((revenue - cost) / cost) * 100
        return {"roi": roi}


class OrchestratorEngine:
    def __init__(
        self,
        db: Session,
        work_service: WorkService,
        event_service: EventService,
    ) -> None:
        self.db = db
        self.work_service = work_service
        self.event_service = event_service
        self.routing = RoutingEngine()
        self.juridico = JuridicoService()
        self.cefida = CefeidaService()
        self.cea = CeaService()
        self._plugins: dict[str, Callable[[WorkItem], Any]] = {}

    def register_monolith(self, name: str, handler: Callable[[WorkItem], Any]) -> None:
        self._plugins[name] = handler

    def handle(self, work_id: str, user_id: str = "SYSTEM") -> dict[str, Any]:
        work = self.work_service.get(work_id)
        if not work:
            raise ValueError("work_not_found")

        if not self.juridico.validate(work):
            self._audit(user_id=user_id, action="work_blocked_legal_gate", entity_id=work.id)
            return {"status": "blocked", "reason": "legal_gate"}

        market = self.cefida.analyze(work)
        finance = self.cea.calculate(work)
        priority_score = float(market.get("score", 0.0)) + float(finance.get("roi", 0.0))

        work.priority_score = priority_score
        work.status = "review" if priority_score < 0 else "in_progress"
        work.updated_at = datetime.now(timezone.utc)
        self.db.add(work)
        self.db.commit()
        self.db.refresh(work)

        decision = "approve" if priority_score >= 0 else "reject"
        self.event_service.emit(
            "decision.made",
            {"work_id": work.id, "decision": decision, "priority_score": priority_score},
            source="orchestrator",
        )

        dispatch_result = None
        if decision == "approve":
            dispatch_result = self.dispatch(work)

        self._audit(user_id=user_id, action="work_processed", entity_id=work.id)
        return {
            "status": "processed",
            "work_id": work.id,
            "decision": decision,
            "priority_score": priority_score,
            "market": market,
            "finance": finance,
            "dispatch": dispatch_result,
        }

    def dispatch(self, work: WorkItem) -> dict[str, Any]:
        target = self.routing.route(work)
        payload = {"work_id": work.id, "target_monolith": target}
        self.event_service.emit("work.assigned", payload, source="orchestrator")

        handler = self._plugins.get(target)
        plugin_result = None
        if handler:
            plugin_result = handler(work)

        return {"target": target, "plugin_result": plugin_result}

    def subscribe_work_created(self, bus: RedisEventBus | InMemoryEventBus) -> None:
        def _on_work_created(message: dict[str, Any]) -> None:
            event = message.get("event", {}) if isinstance(message, dict) else {}
            work_id = event.get("work_id") if isinstance(event, dict) else None
            if not work_id:
                return
            try:
                self.handle(work_id)
            except Exception:
                return

        bus.subscribe("work.created", _on_work_created)

    def heartbeat_once(self) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        entries = self.db.query(MonolithRegistry).all()
        for entry in entries:
            entry.last_heartbeat = now
            self.db.add(entry)
            count += 1
        self.db.commit()
        return count

    async def heartbeat_loop(self, interval_seconds: int = 5) -> None:
        while True:
            self.heartbeat_once()
            await asyncio.sleep(interval_seconds)

    def _audit(self, user_id: str, action: str, entity_id: str) -> None:
        self.db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                entity_type="work_item",
                entity_id=entity_id,
            )
        )
        self.db.commit()


class LiceuSDKRuntime:
    def __init__(self, work: WorkService, events: EventService, orchestrator: OrchestratorEngine) -> None:
        self.work = work
        self.events = events
        self.orchestrator = orchestrator


def build_liceu_sdk(db: Session, bus: RedisEventBus | InMemoryEventBus) -> LiceuSDKRuntime:
    event_service = EventService(db, bus)
    work_service = WorkService(db, event_service)
    orchestrator = OrchestratorEngine(db, work_service, event_service)
    return LiceuSDKRuntime(work=work_service, events=event_service, orchestrator=orchestrator)

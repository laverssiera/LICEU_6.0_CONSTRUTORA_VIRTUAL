from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.core.market_duality import ROLE_MONOLITH_ACCESS, UserIdentity, normalize_role
from app.internal.event_bus import InMemoryEventBus, RedisEventBus
from app.models.orchestration import (
    AuditLog,
    KanbanActor,
    KanbanAttachment,
    KanbanAudit,
    KanbanCard,
    KanbanComment,
    KanbanEvent,
    KanbanJohn,
    KanbanSyncState,
    Workspace,
    WorkspaceUser,
)

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

KANBAN_STAGES = ["leads", "negotiation", "proposal", "juridico", "closed"]
STAGE_ORDER = {stage: index for index, stage in enumerate(KANBAN_STAGES)}
MONOLITH_STAGE_VIEWS = {
    "archimedes": {"leads", "negotiation", "proposal", "closed"},
    "juridicotech": {"proposal", "juridico"},
    "hubbackoffice": {"juridico", "closed"},
    "john": set(KANBAN_STAGES),
}
IGNORED_EVENT_PREFIXES = ("kanban.", "work.", "growth.")
IGNORED_EVENT_TYPES = {"john.welcome"}
WORKSPACE_ALLOWED_ROLES = {
    "SUPER_ADMIN",
    "DIRETOR",
    "FINANCEIRO",
    "ENGENHARIA",
    "QUALIDADE",
    "AUDITOR",
    "GERENTE",
    "FORNECEDOR",
    "CLIENTE",
    "COLABORADOR",
}
ROLE_VIEW_ALL = {"SUPER_ADMIN", "DIRETOR", "ENGENHARIA", "AUDITOR"}


def _normalize_source(source: str | None) -> str:
    return (source or "core_os").strip().lower().replace("-", "_")


def should_project_event(event_type: str) -> bool:
    normalized = (event_type or "").strip().lower()
    if not normalized:
        return False
    if normalized in IGNORED_EVENT_TYPES:
        return False
    return not normalized.startswith(IGNORED_EVENT_PREFIXES)


def resolve_entity_key(event_type: str, payload: dict[str, Any]) -> tuple[str, str]:
    candidates = [
        ("deal", payload.get("deal_id")),
        ("lead", payload.get("lead_id")),
        ("project", payload.get("project_id")),
        ("contract", payload.get("contract_id")),
        ("proposal", payload.get("proposal_id")),
        ("campaign", payload.get("campaign_id")),
        ("property", payload.get("property_id")),
    ]

    for entity_type, value in candidates:
        if value:
            return entity_type, f"{entity_type}_{value}"

    fallback_type = (event_type.split(".", 1)[0] or "entity").replace("-", "_")
    fallback_value = payload.get("id") or payload.get("title") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return fallback_type, f"{fallback_type}_{fallback_value}"


def resolve_stage(event_type: str, payload: dict[str, Any]) -> str:
    stage_map = {
        "lead.created": "leads",
        "match.generated": "negotiation",
        "deal.created": "negotiation",
        "deal.closed": "negotiation",
        "proposal.sent": "proposal",
        "contract.created": "juridico",
        "contract.signed": "juridico",
        "commission.protected": "juridico",
        "payment.generated": "closed",
    }
    explicit_stage = payload.get("stage")
    if isinstance(explicit_stage, str) and explicit_stage in STAGE_ORDER:
        return explicit_stage
    return stage_map.get(event_type, "leads")


def resolve_title(entity_type: str, payload: dict[str, Any]) -> str:
    for field in ("title", "property_title", "project_name", "name"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for field in ("deal_id", "lead_id", "contract_id", "proposal_id", "project_id"):
        value = payload.get(field)
        if value:
            return f"{entity_type.title()} {value}"

    return entity_type.title()


def merge_status_map(current: dict[str, Any], event_type: str) -> dict[str, Any]:
    merged = {
        "juridico": current.get("juridico", "pending"),
        "financeiro": current.get("financeiro", "pending"),
        "marketing": current.get("marketing", "idle"),
    }

    if event_type == "campaign.triggered":
        merged["marketing"] = "active"
    if event_type == "proposal.sent":
        merged["juridico"] = "pending"
    if event_type == "contract.created":
        merged["juridico"] = "active"
    if event_type in {"contract.signed", "commission.protected"}:
        merged["juridico"] = "ok"
    if event_type == "deal.closed":
        merged["financeiro"] = "pending"
    if event_type == "payment.generated":
        merged["financeiro"] = "ok"

    return merged


def build_john_summary(stage: str, risk_level: str, payload: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("john"), dict):
        return payload["john"]

    action_map = {
        "leads": "qualificar lead",
        "negotiation": "ligar agora",
        "proposal": "acompanhar proposta",
        "juridico": "validar contrato e assinatura",
        "closed": "acompanhar entrega e pós-venda",
    }
    confidence_map = {
        "leads": 0.72,
        "negotiation": 0.79,
        "proposal": 0.82,
        "juridico": 0.88,
        "closed": 0.93,
    }

    return {
        "action": action_map.get(stage, current.get("action", "revisar card")),
        "confidence": confidence_map.get(stage, current.get("confidence", 0.7)),
        "risk": risk_level,
    }


def decimal_to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


class KanbanService:
    def __init__(self, db: Session, bus: RedisEventBus | InMemoryEventBus) -> None:
        self.db = db
        self.bus = bus

    def ingest_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "core_os",
        occurred_at: datetime | None = None,
        emit_update: bool = True,
    ) -> dict[str, Any] | None:
        normalized_type = (event_type or "").strip().lower()
        if not should_project_event(normalized_type):
            return None

        entity_type, entity_key = resolve_entity_key(normalized_type, payload)
        card = self.db.query(KanbanCard).filter(KanbanCard.entity_key == entity_key).first()
        if card is None:
            card = KanbanCard(entity_key=entity_key, entity_type=entity_type)
            self.db.add(card)
            self.db.flush()

        target_stage = resolve_stage(normalized_type, payload)
        current_stage_rank = STAGE_ORDER.get(card.stage or "leads", 0)
        target_stage_rank = STAGE_ORDER.get(target_stage, 0)
        if target_stage_rank >= current_stage_rank:
            card.stage = target_stage

        card.entity_type = entity_type
        card.title = resolve_title(entity_type, payload)
        card.source = _normalize_source(source)
        card.owner = payload.get("owner") or card.owner
        card.assigned_to = payload.get("assigned_to") or payload.get("owner") or card.assigned_to
        card.monetary_value = payload.get("value") or payload.get("amount") or payload.get("price") or card.monetary_value or 0
        card.risk_level = str(payload.get("risk") or card.risk_level or "unknown")

        merged_context = dict(card.context or {})
        merged_context.update(payload)

        alerts = list(merged_context.get("alerts") or [])
        if normalized_type in {"bypass.detected", "client.silent", "contract.pending"} and normalized_type not in alerts:
            alerts.append(normalized_type)
        merged_context["alerts"] = alerts
        merged_context["last_event_type"] = normalized_type
        card.context = merged_context

        card.status_map = merge_status_map(dict(card.status_map or {}), normalized_type)
        card.john_summary = build_john_summary(card.stage, card.risk_level, payload, dict(card.john_summary or {}))
        card.updated_at = datetime.now(timezone.utc)

        john_row = self.db.query(KanbanJohn).filter(KanbanJohn.card_id == card.id).first()
        if john_row is None:
            john_row = KanbanJohn(card_id=card.id)
            self.db.add(john_row)
        john_row.suggestion = str(card.john_summary.get("action") or "revisar card")
        john_row.confidence = float(card.john_summary.get("confidence") or 0.0)
        john_row.risk = str(card.john_summary.get("risk") or card.risk_level or "unknown")
        john_row.updated_at = datetime.now(timezone.utc)

        card_event = KanbanEvent(
            card_id=card.id,
            event_type=normalized_type,
            payload=payload,
            source=_normalize_source(source),
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        self.db.add(card_event)

        actor = self.db.query(KanbanActor).filter(
            KanbanActor.card_id == card.id,
            KanbanActor.monolith == _normalize_source(source),
        ).first()
        if actor is None:
            actor = KanbanActor(card_id=card.id, monolith=_normalize_source(source), status="active")
            self.db.add(actor)
        else:
            actor.status = "active"
            actor.updated_at = datetime.now(timezone.utc)

        self.db.add(
            KanbanAudit(
                user_id=None,
                action=f"kanban.event.ingest.{normalized_type}",
                card_id=card.id,
            )
        )

        self.db.commit()
        self.db.refresh(card)

        snapshot = self.serialize_card(card.id)
        if emit_update and snapshot is not None:
            self.bus.publish(settings.KANBAN_EVENT_CHANNEL, snapshot)

        return snapshot

    def serialize_card(self, card_id: str) -> dict[str, Any] | None:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            return None

        events = (
            self.db.query(KanbanEvent)
            .filter(KanbanEvent.card_id == card.id)
            .order_by(KanbanEvent.occurred_at.asc())
            .all()
        )
        actors = (
            self.db.query(KanbanActor)
            .filter(KanbanActor.card_id == card.id)
            .order_by(KanbanActor.monolith.asc())
            .all()
        )
        comments = (
            self.db.query(KanbanComment)
            .filter(KanbanComment.card_id == card.id)
            .order_by(KanbanComment.created_at.asc())
            .all()
        )
        attachments = (
            self.db.query(KanbanAttachment)
            .filter(KanbanAttachment.card_id == card.id)
            .order_by(KanbanAttachment.created_at.asc())
            .all()
        )

        return {
            "id": card.id,
            "entity_key": card.entity_key,
            "entity_type": card.entity_type,
            "title": card.title,
            "stage": card.stage,
            "source": card.source,
            "assigned_to": card.assigned_to,
            "owner": card.owner,
            "value": decimal_to_float(card.monetary_value),
            "risk": card.risk_level,
            "status": card.status_map or {},
            "john": card.john_summary or {},
            "alerts": list((card.context or {}).get("alerts") or []),
            "context": card.context or {},
            "events": [item.event_type for item in events],
            "timeline": [
                {
                    "id": item.id,
                    "event_type": item.event_type,
                    "source": item.source,
                    "payload": item.payload,
                    "timestamp": item.occurred_at.isoformat() if item.occurred_at else None,
                }
                for item in events
            ],
            "actors": [
                {
                    "monolith": actor.monolith,
                    "status": actor.status,
                    "updated_at": actor.updated_at.isoformat() if actor.updated_at else None,
                }
                for actor in actors
            ],
            "comments": [
                {
                    "id": comment.id,
                    "author": comment.author,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                }
                for comment in comments
            ],
            "attachments": [
                {
                    "id": attachment.id,
                    "uploaded_by": attachment.uploaded_by,
                    "file_name": attachment.file_name,
                    "file_url": attachment.file_url,
                    "media_type": attachment.media_type,
                    "created_at": attachment.created_at.isoformat() if attachment.created_at else None,
                }
                for attachment in attachments
            ],
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        }

    def list_cards(
        self,
        *,
        monolith_view: str | None = None,
        assigned_to: str | None = None,
        risk: str | None = None,
        min_value: float | None = None,
        stage: str | None = None,
        owner: str | None = None,
    ) -> list[dict[str, Any]]:
        query = self.db.query(KanbanCard)

        if stage:
            query = query.filter(KanbanCard.stage == stage)
        if assigned_to:
            query = query.filter(KanbanCard.assigned_to == assigned_to)
        if owner:
            query = query.filter(KanbanCard.owner == owner)
        if risk:
            query = query.filter(KanbanCard.risk_level == risk)
        if min_value is not None:
            query = query.filter(KanbanCard.monetary_value >= min_value)

        cards = query.order_by(KanbanCard.created_at.desc()).all()
        snapshots = [self.serialize_card(card.id) for card in cards]
        items = [snapshot for snapshot in snapshots if snapshot is not None]

        if monolith_view:
            allowed_stages = MONOLITH_STAGE_VIEWS.get(monolith_view.lower())
            if allowed_stages is not None:
                items = [item for item in items if item["stage"] in allowed_stages]

        return items

    def board(self, **filters: Any) -> dict[str, Any]:
        cards = self.list_cards(**filters)
        columns = {stage: [] for stage in KANBAN_STAGES}
        for card in cards:
            columns.setdefault(card["stage"], []).append(card)

        totals = {stage: len(columns.get(stage, [])) for stage in KANBAN_STAGES}
        total_cards = len(cards)
        closed_count = totals.get("closed", 0)
        conversion_rate = 0.0 if total_cards == 0 else round((closed_count / total_cards) * 100, 2)

        return {
            "columns": [
                {"id": stage, "title": stage.upper(), "items": columns.get(stage, [])}
                for stage in KANBAN_STAGES
            ],
            "totals": totals,
            "kpis": {
                "total_cards": total_cards,
                "closed_cards": closed_count,
                "conversion_rate": conversion_rate,
                "high_risk_cards": len([card for card in cards if card.get("risk") == "high"]),
            },
        }

    def apply_visibility(self, items: list[dict[str, Any]], identity: UserIdentity) -> list[dict[str, Any]]:
        workspace_user = self.resolve_workspace_user(identity)
        role = workspace_user.role if workspace_user is not None else self.resolve_identity_role(identity)
        principal = workspace_user.id if workspace_user is not None else identity.username

        filtered = [item for item in items if self.can_view_card(role, principal, item)]
        return filtered

    def enforce_card_access(self, card: KanbanCard, identity: UserIdentity) -> None:
        workspace_user = self.resolve_workspace_user(identity)
        role = workspace_user.role if workspace_user is not None else self.resolve_identity_role(identity)
        principal = workspace_user.id if workspace_user is not None else identity.username

        if self.can_manage_card(role, principal, self.serialize_card(card.id) or {}):
            return

        raise PermissionError("access_denied")

    def ensure_workspace(self) -> Workspace:
        workspace = self.db.query(Workspace).order_by(Workspace.created_at.asc()).first()
        if workspace is None:
            workspace = Workspace(name="LICEU 6.0 Workspace", max_users=10)
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
        return workspace

    def list_workspace_users(self) -> list[dict[str, Any]]:
        workspace = self.ensure_workspace()
        users = (
            self.db.query(WorkspaceUser)
            .filter(WorkspaceUser.workspace_id == workspace.id)
            .order_by(WorkspaceUser.created_at.asc())
            .all()
        )
        return [
            {
                "id": item.id,
                "workspace_id": item.workspace_id,
                "external_username": item.external_username,
                "name": item.name,
                "email": item.email,
                "role": item.role,
                "active": item.active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in users
        ]

    def add_workspace_user(
        self,
        *,
        name: str,
        email: str,
        role: str,
        external_username: str | None,
        actor: str,
    ) -> dict[str, Any]:
        workspace = self.ensure_workspace()
        normalized_role = normalize_role(role)
        if normalized_role not in WORKSPACE_ALLOWED_ROLES:
            raise ValueError("invalid_role")

        active_count = (
            self.db.query(WorkspaceUser)
            .filter(WorkspaceUser.workspace_id == workspace.id, WorkspaceUser.active.is_(True))
            .count()
        )
        if active_count >= workspace.max_users:
            raise ValueError("workspace_user_limit_reached")

        existing_email = self.db.query(WorkspaceUser).filter(WorkspaceUser.email == email).first()
        if existing_email is not None:
            raise ValueError("email_already_exists")

        if external_username:
            existing_username = (
                self.db.query(WorkspaceUser)
                .filter(WorkspaceUser.external_username == external_username)
                .first()
            )
            if existing_username is not None:
                raise ValueError("username_already_exists")

        user = WorkspaceUser(
            workspace_id=workspace.id,
            external_username=external_username,
            name=name,
            email=email,
            role=normalized_role,
            active=True,
        )
        self.db.add(user)
        self.db.flush()
        self.db.add(
            AuditLog(
                user_id=actor,
                action=f"workspace.user.created.{normalized_role}",
                entity_type="workspace_user",
                entity_id=user.id,
            )
        )
        self.db.commit()
        self.db.refresh(user)

        return {
            "id": user.id,
            "workspace_id": user.workspace_id,
            "external_username": user.external_username,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "active": user.active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    def resolve_workspace_user(self, identity: UserIdentity) -> WorkspaceUser | None:
        return (
            self.db.query(WorkspaceUser)
            .filter(WorkspaceUser.external_username == identity.username, WorkspaceUser.active.is_(True))
            .first()
        )

    def resolve_identity_role(self, identity: UserIdentity) -> str:
        role = normalize_role(identity.role)
        if role in WORKSPACE_ALLOWED_ROLES:
            return role
        if "workspace:internal" in identity.scopes:
            return "SUPER_ADMIN"
        return "COLABORADOR"

    def _role_can_access_monolith(self, role: str, source: str | None) -> bool:
        normalized_role = normalize_role(role)
        allowed_monoliths = ROLE_MONOLITH_ACCESS.get(normalized_role, [])
        if "*" in allowed_monoliths:
            return True

        normalized_source = str(source or "").strip().lower()
        return normalized_source in {item.lower() for item in allowed_monoliths}

    def can_view_card(self, role: str, principal: str, card: dict[str, Any]) -> bool:
        normalized_role = normalize_role(role)
        if not self._role_can_access_monolith(normalized_role, card.get("source")):
            return False
        if normalized_role in ROLE_VIEW_ALL:
            return True
        if normalized_role == "FORNECEDOR":
            return card.get("owner") == principal or card.get("assigned_to") == principal
        if normalized_role == "QUALIDADE":
            return card.get("stage") in {"juridico", "proposal"}
        if normalized_role == "FINANCEIRO":
            return card.get("stage") == "closed"
        if normalized_role in {"GERENTE", "CLIENTE", "COLABORADOR"}:
            return card.get("owner") == principal or card.get("assigned_to") == principal
        return card.get("owner") == principal or card.get("assigned_to") == principal

    def can_manage_card(self, role: str, principal: str, card: dict[str, Any]) -> bool:
        normalized_role = normalize_role(role)
        if not self._role_can_access_monolith(normalized_role, card.get("source")):
            return False
        if normalized_role in ROLE_VIEW_ALL:
            return True
        if normalized_role == "FORNECEDOR":
            return card.get("owner") == principal or card.get("assigned_to") == principal
        if normalized_role == "QUALIDADE":
            return card.get("stage") in {"juridico", "proposal"}
        if normalized_role == "FINANCEIRO":
            return card.get("stage") == "closed"
        if normalized_role in {"GERENTE", "CLIENTE", "COLABORADOR"}:
            return card.get("owner") == principal or card.get("assigned_to") == principal
        return card.get("owner") == principal or card.get("assigned_to") == principal

    def assign_card(self, card_id: str, assigned_to: str, identity: UserIdentity) -> dict[str, Any]:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise ValueError("card_not_found")

        self.enforce_card_access(card, identity)
        card.assigned_to = assigned_to
        card.updated_at = datetime.now(timezone.utc)
        self.db.add(card)
        self.db.add(
            AuditLog(
                user_id=identity.username,
                action="kanban.card.assigned",
                entity_type="kanban_card",
                entity_id=card.id,
            )
        )
        self.db.add(
            KanbanAudit(
                user_id=identity.username,
                action="kanban.card.assigned",
                card_id=card.id,
            )
        )
        self.db.commit()
        self.db.refresh(card)
        snapshot = self.serialize_card(card.id)
        if snapshot is not None:
            self.bus.publish(settings.KANBAN_EVENT_CHANNEL, snapshot)
        return snapshot or {}

    def add_comment(self, card_id: str, content: str, identity: UserIdentity) -> dict[str, Any]:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise ValueError("card_not_found")
        self.enforce_card_access(card, identity)

        comment = KanbanComment(card_id=card.id, author=identity.username, content=content)
        self.db.add(comment)
        self.db.add(
            AuditLog(
                user_id=identity.username,
                action="kanban.card.comment",
                entity_type="kanban_card",
                entity_id=card.id,
            )
        )
        self.db.add(
            KanbanAudit(
                user_id=identity.username,
                action="kanban.card.comment",
                card_id=card.id,
            )
        )
        self.db.commit()
        snapshot = self.serialize_card(card.id)
        if snapshot is not None:
            self.bus.publish(settings.KANBAN_EVENT_CHANNEL, snapshot)
        return snapshot or {}

    def add_attachment(
        self,
        card_id: str,
        *,
        file_name: str,
        file_url: str,
        media_type: str,
        identity: UserIdentity,
    ) -> dict[str, Any]:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise ValueError("card_not_found")
        self.enforce_card_access(card, identity)

        attachment = KanbanAttachment(
            card_id=card.id,
            uploaded_by=identity.username,
            file_name=file_name,
            file_url=file_url,
            media_type=media_type,
        )
        self.db.add(attachment)
        self.db.add(
            AuditLog(
                user_id=identity.username,
                action="kanban.card.attachment",
                entity_type="kanban_card",
                entity_id=card.id,
            )
        )
        self.db.add(
            KanbanAudit(
                user_id=identity.username,
                action="kanban.card.attachment",
                card_id=card.id,
            )
        )
        self.db.commit()
        snapshot = self.serialize_card(card.id)
        if snapshot is not None:
            self.bus.publish(settings.KANBAN_EVENT_CHANNEL, snapshot)
        return snapshot or {}

    def run_automation(self, card_id: str, automation: str, identity: UserIdentity) -> dict[str, Any]:
        card = self.db.query(KanbanCard).filter(KanbanCard.id == card_id).first()
        if card is None:
            raise ValueError("card_not_found")
        self.enforce_card_access(card, identity)

        context = dict(card.context or {})
        alerts = list(context.get("alerts") or [])

        if automation == "contract_signed_to_finance" and "contract.signed" in [
            item.event_type
            for item in self.db.query(KanbanEvent).filter(KanbanEvent.card_id == card.id).all()
        ]:
            card.stage = "juridico"
            card.status_map = merge_status_map(dict(card.status_map or {}), "contract.signed")

        if automation == "payment_generated_to_closed" and "payment.generated" in [
            item.event_type
            for item in self.db.query(KanbanEvent).filter(KanbanEvent.card_id == card.id).all()
        ]:
            card.stage = "closed"
            card.status_map = merge_status_map(dict(card.status_map or {}), "payment.generated")

        if automation == "contract_pending_alert" and "contract.created" in [
            item.event_type
            for item in self.db.query(KanbanEvent).filter(KanbanEvent.card_id == card.id).all()
        ]:
            if "contract.pending" not in alerts:
                alerts.append("contract.pending")

        context["alerts"] = alerts
        card.context = context
        card.updated_at = datetime.now(timezone.utc)
        self.db.add(card)
        self.db.add(
            AuditLog(
                user_id=identity.username,
                action=f"kanban.card.automation.{automation}",
                entity_type="kanban_card",
                entity_id=card.id,
            )
        )
        self.db.add(
            KanbanAudit(
                user_id=identity.username,
                action=f"kanban.card.automation.{automation}",
                card_id=card.id,
            )
        )
        self.db.commit()

        snapshot = self.serialize_card(card.id)
        if snapshot is not None:
            self.bus.publish(settings.KANBAN_EVENT_CHANNEL, snapshot)
        return snapshot or {}

    def sync_runtime_events(self, redis_url: str, stream_name: str, limit: int = 100) -> dict[str, Any]:
        if redis is None:
            raise RuntimeError("redis_client_unavailable")

        client = redis.Redis.from_url(redis_url, decode_responses=True)
        state = self.db.query(KanbanSyncState).filter(KanbanSyncState.stream_name == stream_name).first()
        if state is None:
            state = KanbanSyncState(stream_name=stream_name, last_id="0-0")
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)

        entries = client.xread({stream_name: state.last_id}, count=limit, block=1)
        processed = 0
        cards_updated = 0

        for _, messages in entries:
            for entry_id, fields in messages:
                event_blob = fields.get("event")
                event_payload = json.loads(event_blob) if isinstance(event_blob, str) else {}
                event_type = str(event_payload.get("type") or "").strip().lower()
                payload = event_payload.get("payload") if isinstance(event_payload.get("payload"), dict) else {}
                source = str(event_payload.get("source") or "runtime")

                if event_type:
                    snapshot = self.ingest_event(event_type, payload, source=source)
                    if snapshot is not None:
                        cards_updated += 1

                state.last_id = entry_id
                state.updated_at = datetime.now(timezone.utc)
                processed += 1

        self.db.add(state)
        self.db.commit()
        return {
            "stream": stream_name,
            "last_id": state.last_id,
            "processed": processed,
            "cards_updated": cards_updated,
        }
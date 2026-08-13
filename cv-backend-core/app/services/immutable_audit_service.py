from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.orchestration import ImmutableAuditLog


class ImmutableAuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def append(
        self,
        *,
        entity_type: str,
        entity_id: str | None,
        action: str,
        actor: str = "system",
        payload: dict[str, Any] | None = None,
    ) -> ImmutableAuditLog:
        previous = (
            self.db.query(ImmutableAuditLog)
            .order_by(ImmutableAuditLog.created_at.desc(), ImmutableAuditLog.id.desc())
            .first()
        )
        created_at = datetime.now(timezone.utc)
        previous_hash = previous.hash_value if previous else None
        normalized_payload = payload or {}
        hash_value = self._compute_hash(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            payload=normalized_payload,
            previous_hash=previous_hash,
            created_at=created_at,
        )

        item = ImmutableAuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            payload=normalized_payload,
            previous_hash=previous_hash,
            hash_value=hash_value,
            created_at=created_at,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def list_logs(
        self,
        *,
        limit: int = 100,
        action: str | None = None,
        entity_id: str | None = None,
        actor: str | None = None,
    ) -> list[ImmutableAuditLog]:
        query = self.db.query(ImmutableAuditLog)
        if action:
            query = query.filter(ImmutableAuditLog.action == action)
        if entity_id:
            query = query.filter(ImmutableAuditLog.entity_id == entity_id)
        if actor:
            query = query.filter(ImmutableAuditLog.actor == actor)
        return query.order_by(ImmutableAuditLog.created_at.desc()).limit(limit).all()

    def verify_chain(self) -> dict[str, Any]:
        items = self.db.query(ImmutableAuditLog).all()

        broken_ids: list[str] = []
        if not items:
            return {"valid": True, "total": 0, "broken_ids": [], "last_hash": None}

        by_prev: dict[str | None, list[ImmutableAuditLog]] = {}
        for item in items:
            by_prev.setdefault(item.previous_hash, []).append(item)

        roots = by_prev.get(None, [])
        if len(roots) != 1:
            broken_ids.extend(item.id for item in roots)

        current = roots[0] if roots else None
        visited: set[str] = set()
        last_hash: str | None = None

        while current is not None:
            if current.id in visited:
                broken_ids.append(current.id)
                break

            visited.add(current.id)
            recalculated = self._compute_hash(
                entity_type=current.entity_type,
                entity_id=current.entity_id,
                action=current.action,
                actor=current.actor,
                payload=current.payload or {},
                previous_hash=current.previous_hash,
                created_at=current.created_at,
            )
            if current.hash_value != recalculated:
                broken_ids.append(current.id)

            children = by_prev.get(current.hash_value, [])
            if len(children) > 1:
                broken_ids.extend(item.id for item in children)
                break

            last_hash = current.hash_value
            current = children[0] if children else None

        if len(visited) != len(items):
            for item in items:
                if item.id not in visited:
                    broken_ids.append(item.id)

        dedup_broken_ids = list(dict.fromkeys(broken_ids))
        return {
            "valid": len(dedup_broken_ids) == 0,
            "total": len(items),
            "broken_ids": dedup_broken_ids,
            "last_hash": last_hash,
        }

    def _compute_hash(
        self,
        *,
        entity_type: str,
        entity_id: str | None,
        action: str,
        actor: str,
        payload: dict[str, Any],
        previous_hash: str | None,
        created_at: datetime | None,
    ) -> str:
        canonical = json.dumps(
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "actor": actor,
                "payload": payload,
                "previous_hash": previous_hash,
                "created_at": self._normalize_datetime(created_at),
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _normalize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        normalized = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        normalized = normalized.astimezone(timezone.utc)
        return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def serialize_immutable_audit_log(item: ImmutableAuditLog) -> dict[str, Any]:
    return {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "action": item.action,
        "actor": item.actor,
        "payload": item.payload or {},
        "previous_hash": item.previous_hash,
        "hash_value": item.hash_value,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

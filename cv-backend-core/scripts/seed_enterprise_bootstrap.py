from __future__ import annotations

import sys
import uuid
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal


def _fetch_id(db, table: str, where_col: str, where_val: str) -> str | None:
    row = db.execute(
        text(f"SELECT id FROM {table} WHERE {where_col} = :where_val LIMIT 1"),
        {"where_val": where_val},
    ).fetchone()
    return row[0] if row else None


def _insert_if_missing(db, table: str, values: dict, where_col: str, where_val: str) -> str:
    existing_id = _fetch_id(db, table, where_col, where_val)
    if existing_id:
        return existing_id

    values = dict(values)
    values.setdefault("id", str(uuid.uuid4()))

    cols = ", ".join(values.keys())
    params = ", ".join(f":{k}" for k in values)
    db.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({params})"), values)
    return values["id"]


def main() -> None:
    db = SessionLocal()
    try:
        org_id = _insert_if_missing(
            db,
            "organizations",
            {"name": "LICEU Holding", "type": "holding"},
            "name",
            "LICEU Holding",
        )

        admin_id = _insert_if_missing(
            db,
            "users",
            {
                "organization_id": org_id,
                "name": "Admin Master",
                "email": "admin@liceu60.com.br",
                "role": "ADMIN_MASTER",
                "status": "active",
            },
            "email",
            "admin@liceu60.com.br",
        )

        role_names = ["ADMIN_MASTER", "BROKER", "CLIENT", "OWNER", "INVESTOR", "SYSTEM"]
        permission_names = [
            "work.create",
            "work.update",
            "work.assign",
            "work.read",
            "events.emit",
            "events.read",
            "orchestrator.run",
            "audit.read",
            "monolith.manage",
            "contract.approve",
            "finance.read",
        ]

        role_ids: dict[str, str] = {}
        for role_name in role_names:
            role_ids[role_name] = _insert_if_missing(
                db,
                "roles",
                {"name": role_name},
                "name",
                role_name,
            )

        permission_ids: dict[str, str] = {}
        for permission_name in permission_names:
            permission_ids[permission_name] = _insert_if_missing(
                db,
                "permissions",
                {"name": permission_name},
                "name",
                permission_name,
            )

        admin_role_id = role_ids["ADMIN_MASTER"]
        admin_link_id = db.execute(
            text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id LIMIT 1"),
            {"user_id": admin_id, "role_id": admin_role_id},
        ).fetchone()
        if not admin_link_id:
            db.execute(
                text("INSERT INTO user_roles (id, user_id, role_id) VALUES (:id, :user_id, :role_id)"),
                {"id": str(uuid.uuid4()), "user_id": admin_id, "role_id": admin_role_id},
            )

        role_permissions_map = {
            "ADMIN_MASTER": [
                "work.create",
                "work.update",
                "work.assign",
                "work.read",
                "events.emit",
                "events.read",
                "orchestrator.run",
                "audit.read",
                "monolith.manage",
                "contract.approve",
                "finance.read",
            ],
            "BROKER": ["work.create", "work.update", "work.assign", "work.read", "events.read"],
            "CLIENT": ["work.read"],
            "OWNER": ["work.read", "contract.approve"],
            "INVESTOR": ["work.read", "finance.read"],
            "SYSTEM": ["work.read", "events.emit", "orchestrator.run"],
        }

        role_perm_count = 0
        for role_name, perm_list in role_permissions_map.items():
            role_id = role_ids[role_name]
            for perm_name in perm_list:
                perm_id = permission_ids[perm_name]
                exists = db.execute(
                    text(
                        "SELECT id FROM role_permissions "
                        "WHERE role_id = :role_id AND permission_id = :permission_id LIMIT 1"
                    ),
                    {"role_id": role_id, "permission_id": perm_id},
                ).fetchone()
                if not exists:
                    db.execute(
                        text(
                            "INSERT INTO role_permissions (id, role_id, permission_id) "
                            "VALUES (:id, :role_id, :permission_id)"
                        ),
                        {"id": str(uuid.uuid4()), "role_id": role_id, "permission_id": perm_id},
                    )
                role_perm_count += 1

        db.commit()
        print(
            {
                "status": "ok",
                "organization_id": org_id,
                "admin_user_id": admin_id,
                "roles": len(role_ids),
                "permissions": len(permission_ids),
                "role_permission_links_targeted": role_perm_count,
            }
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.orchestration import Permission, Role, RolePermission

MANDATORY_ROLES = [
    "ADMIN_MASTER",
    "BROKER",
    "CLIENT",
    "OWNER",
    "INVESTOR",
    "SYSTEM",
]

PERMISSIONS_BY_ROLE = {
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
    ],
    "BROKER": [
        "work.create",
        "work.update",
        "work.assign",
        "work.read",
        "events.read",
    ],
    "CLIENT": [
        "work.read",
    ],
    "OWNER": [
        "work.read",
        "contract.approve",
    ],
    "INVESTOR": [
        "work.read",
        "finance.read",
    ],
    "SYSTEM": [
        "work.read",
        "events.emit",
        "orchestrator.run",
    ],
}


def seed_rbac_defaults(db: Session) -> dict:
    roles_by_name: dict[str, Role] = {}
    permissions_by_name: dict[str, Permission] = {}

    for role_name in MANDATORY_ROLES:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role is None:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
        roles_by_name[role_name] = role

    permission_names = sorted({name for names in PERMISSIONS_BY_ROLE.values() for name in names})
    for permission_name in permission_names:
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if permission is None:
            permission = Permission(name=permission_name)
            db.add(permission)
            db.flush()
        permissions_by_name[permission_name] = permission

    for role_name, permission_names in PERMISSIONS_BY_ROLE.items():
        role = roles_by_name[role_name]
        for permission_name in permission_names:
            permission = permissions_by_name[permission_name]
            existing = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id)
                .first()
            )
            if existing is None:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    db.commit()

    total_links = db.query(RolePermission).count()
    return {
        "roles": len(roles_by_name),
        "permissions": len(permissions_by_name),
        "role_permissions": total_links,
    }

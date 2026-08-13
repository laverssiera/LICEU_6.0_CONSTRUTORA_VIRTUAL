from app.database import SessionLocal
from app.services.rbac_seed import MANDATORY_ROLES, seed_rbac_defaults
from app.models.orchestration import Permission, Role, RolePermission


def test_seed_rbac_defaults_creates_roles_permissions_and_links():
    db = SessionLocal()
    try:
        summary = seed_rbac_defaults(db)

        assert summary["roles"] == len(MANDATORY_ROLES)
        assert summary["permissions"] > 0
        assert summary["role_permissions"] > 0

        roles = db.query(Role).all()
        permissions = db.query(Permission).all()
        links = db.query(RolePermission).all()

        assert len(roles) >= len(MANDATORY_ROLES)
        assert len(permissions) >= 1
        assert len(links) >= 1
    finally:
        db.close()

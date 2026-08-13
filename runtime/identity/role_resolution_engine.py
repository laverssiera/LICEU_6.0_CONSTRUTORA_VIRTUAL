"""
Engine de resolução determinística de papéis e escopos soberanos federados.
- Normalização canônica de papéis
- Validação cross-federation
- Contratos determinísticos de acesso
- Reconciliação de identidade soberana
- Consistência runtime de permissões
"""

CANONICAL_ROLE_MAP = {
    "cliente": "CLIENTE",
    "irmandade": "IRMADNDADE",
    "super_admin": "SUPER_ADMIN",
    "admin": "ADMIN",
    "user": "USER",
    "guest": "GUEST",
}

FEDERATION_ROLE_ALIASES = {
    "IRMADNDADE": ["irmandade", "irmandade_demo", "irmandade_federada"],
    "CLIENTE": ["cliente", "cliente_demo", "cliente_federado"],
    "SUPER_ADMIN": ["super_admin", "admin_master", "federation_admin"],
}

class RoleResolutionEngine:
    @staticmethod
    def normalize_role(role: str) -> str:
        """Normaliza para o papel canônico soberano."""
        role = role.lower()
        for canonical, aliases in FEDERATION_ROLE_ALIASES.items():
            if role in aliases:
                return canonical
        return CANONICAL_ROLE_MAP.get(role, role.upper())

    @staticmethod
    def validate_cross_federation(role: str, federation: str = None) -> bool:
        """Valida se o papel é aceito na federação."""
        norm = RoleResolutionEngine.normalize_role(role)
        # Exemplo: pode expandir para regras de federação
        return norm in CANONICAL_ROLE_MAP.values()

    @staticmethod
    def reconcile_identity(payload: dict) -> dict:
        """Reconcilia e normaliza viewer_role e escopos."""
        if "viewer_role" in payload:
            payload["viewer_role"] = RoleResolutionEngine.normalize_role(payload["viewer_role"])
        if "roles" in payload and isinstance(payload["roles"], list):
            payload["roles"] = [RoleResolutionEngine.normalize_role(r) for r in payload["roles"]]
        return payload

    @staticmethod
    def resolve_permission(role: str, action: str, context: dict = None) -> bool:
        """Resolução determinística de permissão (mock)."""
        norm = RoleResolutionEngine.normalize_role(role)
        # Exemplo: regras reais podem ser implementadas
        if norm == "SUPER_ADMIN":
            return True
        if norm == "IRMADNDADE" and action in {"see_protected_details", "access_internal"}:
            return True
        if norm == "CLIENTE" and action == "see_public_details":
            return True
        return False

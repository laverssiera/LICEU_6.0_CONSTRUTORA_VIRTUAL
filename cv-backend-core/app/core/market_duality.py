from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

CANONICAL_ROLES = {
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
    "IRMADNDADE",
}

LEGACY_ROLE_ALIASES = {
    "EXECUTIVO": "DIRETOR",
    "GESTOR": "DIRETOR",
    "IRMANDADE": "SUPER_ADMIN",
    "OPERACIONAL": "GERENTE",
    "OPERADOR": "GERENTE",
    "VIEWER": "COLABORADOR",
    "CORRETOR": "FORNECEDOR",
    "JURIDICO": "QUALIDADE",
}

ROLE_MONOLITH_ACCESS: dict[str, list[str]] = {
    "SUPER_ADMIN": ["*"],
    "DIRETOR": ["core_os", "cefeida", "econotech", "liceu"],
    "FINANCEIRO": ["hubbackoffice", "cea", "hub", "core_os"],
    "ENGENHARIA": ["opera", "bim", "eng"],
    "QUALIDADE": ["pdi_ia", "anchor", "pd", "p&d"],
    "AUDITOR": ["audit", "hospital"],
    "GERENTE": ["opera"],
    "FORNECEDOR": ["fornecedores"],
    "CLIENTE": ["archimedes", "opera"],
    "COLABORADOR": ["academia_saber", "opera"],
}

ACTION_ALLOWED_ROLES: dict[str, set[str]] = {
    "approve_strategy": {"SUPER_ADMIN", "DIRETOR"},
    "release_payment": {"FINANCEIRO"},
    "execute_work": {"GERENTE"},
    "change_process": {"QUALIDADE"},
    "approve_john_decision": {"SUPER_ADMIN"},
    "create_strategy": {"SUPER_ADMIN", "DIRETOR"},
    "release_capital": {"SUPER_ADMIN", "FINANCEIRO"},
}

FACADE_REGISTRY: dict[str, dict[str, Any]] = {
    "archimedes.liceu.local": {
        "brand": "Archimedes",
        "monolith": "archimedes",
        "visibility": "public",
        "headline": "Ativos imobiliários com inteligência de viabilidade.",
    },
    "cefeida.liceu.local": {
        "brand": "Cefeida",
        "monolith": "cefeida",
        "visibility": "public",
        "headline": "Estratégia, dados e leitura preditiva do mercado.",
    },
    "workspace.liceu.local": {
        "brand": "Liceu Workspace",
        "monolith": "core_os",
        "visibility": "private",
        "headline": "Área integrada da Irmandade e operação segura.",
    },
}

DEMO_USERS: dict[str, dict[str, Any]] = {
    "executivo_acme": {
        "password": "demo123",
        "role": "DIRETOR",
        "roles": ["DIRETOR"],
        "display_name": "Executivo ACME",
        "tenant": "acme",
        "monolith_access": ["core_os", "cefeida", "econotech", "liceu"],
        "scopes": ["market:read", "workspace:internal", "industrial:read", "facade:public"],
    },
    "executivo_demo": {
        "password": "demo123",
        "role": "DIRETOR",
        "roles": ["DIRETOR"],
        "display_name": "Executivo Liceu",
        "tenant": "liceu",
        "monolith_access": ["core_os", "cefeida", "econotech", "liceu"],
        "scopes": ["market:read", "workspace:internal", "industrial:read", "facade:public"],
    },
    "gestor_demo": {
        "password": "demo123",
        "role": "ENGENHARIA",
        "roles": ["ENGENHARIA", "GERENTE"],
        "display_name": "Gestor Liceu",
        "tenant": "liceu",
        "monolith_access": ["opera", "bim", "eng"],
        "scopes": ["market:read", "workspace:internal", "industrial:read", "facade:public"],
    },
    "operacional_demo": {
        "password": "demo123",
        "role": "GERENTE",
        "roles": ["GERENTE"],
        "display_name": "Operacional Liceu",
        "tenant": "liceu",
        "monolith_access": ["opera"],
        "scopes": ["market:read", "workspace:internal", "facade:public"],
    },
    "cliente_demo": {
        "password": "demo123",
        "role": "CLIENTE",
        "roles": ["CLIENTE"],
        "display_name": "Cliente Liceu",
        "tenant": "liceu",
        "monolith_access": ["archimedes", "opera"],
        "scopes": ["market:read", "workspace:client", "facade:public"],
    },
    "irmandade_demo": {
        "password": "demo123",
        "role": "IRMADNDADE",
        "roles": ["IRMADNDADE"],
        "display_name": "Membro da Irmandade",
        "tenant": "liceu",
        "monolith_access": ["*"],
        "scopes": ["market:read", "workspace:internal", "industrial:read", "facade:public"],
    },
}

MARKET_INTELLIGENCE_PAYLOAD: dict[str, Any] = {
    "projected_margin": "18.4%",
    "public_vgv_band": "R$ 48M - R$ 52M",
    "status": "captação assistida",
    "supplier_margin_formula": "indice_composto: aço x prazo x risco logístico",
    "assembly_playbook": "sequenciamento robotizado dfma v3",
    "strategic_note": "substituição de polímero importado por composto reciclado homologado",
}


class SSOLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=64)
    portal: str = Field(default="workspace", min_length=3, max_length=64)


class UserIdentity(BaseModel):
    username: str
    role: str
    roles: list[str] = Field(default_factory=list)
    display_name: str
    portal: str
    tenant: str = "liceu"
    scopes: list[str]
    monolith_access: list[str] = Field(default_factory=list)
    exp: int


def resolve_facade(host: str | None) -> dict[str, Any]:
    normalized = (host or "workspace.liceu.local").split(":")[0].lower().strip()
    return FACADE_REGISTRY.get(
        normalized,
        {
            "brand": "Liceu Workspace",
            "monolith": "core_os",
            "visibility": "private",
            "headline": "Plataforma integrada do ecossistema.",
        },
    )


def _b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _b64decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def issue_access_token(identity: UserIdentity) -> str:
    body = json.dumps(identity.model_dump(), separators=(",", ":"), ensure_ascii=False).encode()
    payload = _b64encode(body)
    signature = hmac.new(settings.SSO_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64encode(signature)}"


def decode_access_token(token: str) -> UserIdentity:
    try:
        payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Token inválido") from exc

    expected = _b64encode(hmac.new(settings.SSO_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    data = json.loads(_b64decode(payload).decode())
    identity = UserIdentity(**data)
    if identity.exp < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Token expirado")
    return identity


def authenticate_user(username: str, password: str, portal: str) -> UserIdentity:
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    exp = int((datetime.now(timezone.utc) + timedelta(minutes=settings.SSO_TOKEN_TTL_MINUTES)).timestamp())
    primary_role = normalize_role(user.get("role"))
    roles = [normalize_role(value) for value in user.get("roles", [user.get("role")])]
    role_set = sorted({primary_role, *roles})
    monolith_access = user.get("monolith_access") or ROLE_MONOLITH_ACCESS.get(primary_role, ["core_os"])

    return UserIdentity(
        username=username,
        role=primary_role,
        roles=role_set,
        display_name=user["display_name"],
        portal=portal,
        tenant=user.get("tenant", "liceu"),
        scopes=user["scopes"],
        monolith_access=monolith_access,
        exp=exp,
    )


def normalize_role(role: str | None) -> str:
    raw = str(role or "").strip().upper()
    if raw in CANONICAL_ROLES:
        return raw
    return LEGACY_ROLE_ALIASES.get(raw, "COLABORADOR")


def resolve_identity_roles(identity: UserIdentity) -> set[str]:
    roles = {normalize_role(identity.role)}
    roles.update(normalize_role(role) for role in identity.roles)
    return roles


def has_any_role(identity: UserIdentity, allowed_roles: set[str]) -> bool:
    normalized_allowed = {normalize_role(role) for role in allowed_roles}
    return bool(resolve_identity_roles(identity).intersection(normalized_allowed))


def require_role(allowed_roles: list[str] | set[str]) -> Callable[[UserIdentity], UserIdentity]:
    normalized_allowed = {normalize_role(role) for role in allowed_roles}

    def dependency(identity: UserIdentity = Depends(get_current_identity)) -> UserIdentity:
        if not has_any_role(identity, normalized_allowed):
            raise HTTPException(status_code=403, detail="Acesso negado")
        return identity

    return dependency


def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserIdentity:
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return decode_access_token(credentials.credentials)


def get_federation_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserIdentity:
    service_secret = settings.CANONICAL_EVENT_STORE_API_SECRET.strip()
    supplied_secret = request.headers.get("X-Canonical-Service-Secret", "")
    if supplied_secret:
        if not service_secret or not hmac.compare_digest(supplied_secret, service_secret):
            raise HTTPException(status_code=401, detail="Credencial de serviço inválida")
        return UserIdentity(
            username="canonical-service",
            role="SUPER_ADMIN",
            roles=["SUPER_ADMIN"],
            display_name="Canonical Federation Service",
            portal="service",
            scopes=["workspace:internal", "workspace:client"],
            monolith_access=["core_os", "econotech"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 300,
        )
    return get_current_identity(credentials)


def require_scope(scope: str) -> Callable[[UserIdentity], UserIdentity]:
    def dependency(identity: UserIdentity = Depends(get_current_identity)) -> UserIdentity:
        if scope not in identity.scopes:
            raise HTTPException(status_code=403, detail="Escopo insuficiente")
        return identity

    return dependency


def filter_market_payload(identity: UserIdentity) -> dict[str, Any]:
    public_keys = ["projected_margin", "public_vgv_band", "status"]
    internal_keys = ["supplier_margin_formula", "assembly_playbook", "strategic_note"]

    if "industrial:read" in identity.scopes:
        return {
            "viewer_role": identity.role,
            "filters": {"industrial_secret": "internal"},
            "data": MARKET_INTELLIGENCE_PAYLOAD,
        }

    filtered = {key: MARKET_INTELLIGENCE_PAYLOAD[key] for key in public_keys}
    return {
        "viewer_role": identity.role,
        "filters": {
            "industrial_secret": "redacted",
            "hidden_fields": internal_keys,
        },
        "data": filtered,
    }


def workspace_modules(identity: UserIdentity) -> list[str]:
    modules = ["portal_cliente", "timeline_obra", "financeiro_resumido"]
    if "workspace:internal" in identity.scopes:
        modules.extend(["cockpit_operacional", "custo_industrial", "segredo_fabrica"])
    return modules


def domain_snapshot(request: Request) -> dict[str, Any]:
    host = request.headers.get("host")
    facade = resolve_facade(host)
    return {
        "host": host,
        **facade,
    }

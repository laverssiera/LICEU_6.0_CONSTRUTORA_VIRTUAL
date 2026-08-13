from typing import List, Dict
from urllib.parse import urlparse
import unicodedata

MONOLITHS: List[Dict[str, str]] = [
    {
        "name": "3C273 CEFEIDA",
        "slug": "cefeida",
        "service": "cefeida-api",
        "db_service": "db_cefeida",
        "domain": "inteligencia_dados",
        "health_path": "/health",
    },
    {
        "name": "P&D.IA",
        "slug": "pdi_ia",
        "service": "pdi-ia-api",
        "db_service": "db_pdi_ia",
        "domain": "pesquisa_ia",
        "health_path": "/health",
    },
    {
        "name": "CORE.OS",
        "slug": "core_os",
        "service": "leme-core",
        "db_service": "db_core_os",
        "domain": "infraestrutura",
        "health_path": "/health/global",
    },
    {
        "name": "BIM.ARQU.ENG",
        "slug": "bim_arqu_eng",
        "service": "bim-arqu-eng-api",
        "db_service": "db_bim_arqu_eng",
        "domain": "engenharia",
        "health_path": "/health",
    },
    {
        "name": "CDVIRTUAL",
        "slug": "cdvirtual",
        "service": "cdvirtual-api",
        "db_service": "db_cdvirtual",
        "domain": "logistica",
        "health_path": "/health",
    },
    {
        "name": "ARCHIMEDES",
        "slug": "archimedes",
        "service": "archimedes-api",
        "db_service": "db_archimedes",
        "domain": "ativos_viabilidade",
        "health_path": "/health",
    },
    {
        "name": "CEA INVESTIMENTOS",
        "slug": "cea_investimentos",
        "service": "cea-investimentos-api",
        "db_service": "db_cea_investimentos",
        "domain": "capital_ri",
        "health_path": "/health",
    },
    {
        "name": "INVEST.TECH",
        "slug": "invest_tech",
        "service": "invest-tech-api",
        "db_service": "db_invest_tech",
        "domain": "captacao_relacoes",
        "health_path": "/health",
    },
    {
        "name": "ECONO.TECH",
        "slug": "econo_tech",
        "service": "econo-tech-api",
        "db_service": "db_econo_tech",
        "domain": "tesouraria_soberana",
        "health_path": "/health",
    },
    {
        "name": "HUB.CONTABIL",
        "slug": "hub_contabil",
        "service": "hub-contabil-api",
        "db_service": "db_hub_contabil",
        "domain": "fiscal_financeiro",
        "health_path": "/health",
    },
    {
        "name": "ERP FORNECEDORES",
        "slug": "erp_fornecedores",
        "service": "erp-fornecedores-api",
        "db_service": "db_erp_fornecedores",
        "domain": "parceiros_supply",
        "health_path": "/health",
    },
    {
        "name": "ACADEMIA DO SABER",
        "slug": "academia_saber",
        "service": "academia-saber-api",
        "db_service": "db_academia_saber",
        "domain": "treinamento",
        "health_path": "/health",
    },
    {
        "name": "GTAMKT",
        "slug": "gtamkt",
        "service": "gtamkt-api",
        "db_service": "db_gtamkt",
        "domain": "marketing_gamificado",
        "health_path": "/health",
    },
    {
        "name": "JURIDICOTECH",
        "slug": "juridicotech",
        "service": "juridicotech-api",
        "db_service": "db_juridicotech",
        "domain": "contratos_compliance",
        "health_path": "/health",
    },
    {
        "name": "JOH BRASILEIRO",
        "slug": "joh_brasileiro",
        "service": "joh-brasileiro-api",
        "db_service": "db_joh_brasileiro",
        "domain": "qualidade_esg",
        "health_path": "/health",
    },
]


_RUNTIME_MONOLITHS: dict[str, Dict[str, str]] = {}

_DOMAIN_CAPABILITIES: dict[str, list[str]] = {
    "infraestrutura": ["gateway_proxy", "registry_lookup", "federated_query", "event_subscription", "telemetry"],
    "inteligencia_dados": ["analytics", "dashboarding", "federated_query", "event_subscription"],
    "pesquisa_ia": ["ai_inference", "cognitive_sync", "event_subscription"],
    "engenharia": ["bim", "orcamento", "planejamento_obra", "event_subscription"],
    "logistica": ["supply_tracking", "fleet_visibility", "event_subscription"],
    "ativos_viabilidade": ["viabilidade", "asset_screening", "event_subscription"],
    "capital_ri": ["captação", "investor_updates", "event_subscription"],
    "captacao_relacoes": ["crm", "fundraising", "event_subscription"],
    "tesouraria_soberana": ["tesouraria", "forecasting", "event_subscription"],
    "fiscal_financeiro": ["contabilidade", "fiscal", "event_subscription"],
    "parceiros_supply": ["supplier_registry", "procurement", "event_subscription"],
    "treinamento": ["academy_plans", "learning_paths", "event_subscription"],
    "marketing_gamificado": ["campaigns", "engagement", "event_subscription"],
    "contratos_compliance": ["contracts", "compliance", "event_subscription"],
    "qualidade_esg": ["quality_audit", "esg_tracking", "event_subscription"],
    "runtime_registered": ["healthcheck", "gateway_proxy", "event_subscription"],
}


def _normalize_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.strip().lower().replace(" ", "_").replace("-", "_")


def _service_from_url(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or fallback or "service").strip().lower().replace("-", "_")


def get_monolith_registry() -> List[Dict[str, str]]:
    merged = {item["slug"]: item.copy() for item in MONOLITHS}
    for slug, item in _RUNTIME_MONOLITHS.items():
        merged[slug] = item.copy()
    return list(merged.values())


def get_monolith_by_slug(slug: str) -> Dict[str, str] | None:
    normalized = _normalize_slug(slug)
    for item in get_monolith_registry():
        if item["slug"] == normalized:
            return item.copy()
        if item.get("service", "").replace("-", "_") == normalized:
            return item.copy()
        if _normalize_slug(item.get("name", "")) == normalized:
            return item.copy()
    return None


def get_monolith_capabilities(slug: str) -> Dict[str, object] | None:
    item = get_monolith_by_slug(slug)
    if item is None:
        return None

    domain = item.get("domain", "runtime_registered")
    capabilities = _DOMAIN_CAPABILITIES.get(domain, ["healthcheck", "gateway_proxy", "event_subscription"])

    return {
        **item,
        "mode": "core" if item["slug"] == "core_os" else "federated",
        "capabilities": capabilities,
        "routes": {
            "health": item.get("health_path", "/health"),
            "gateway_proxy": f"/gateway/proxy/{item['slug']}",
            "event_subscription": f"/events/subscribe/{item['slug']}",
            "federated_query": "/gateway/query",
        },
    }


def register_monolith(payload: Dict[str, str]) -> Dict[str, str]:
    name = payload["name"].strip()
    slug = _normalize_slug(name)
    url = payload["url"].strip()
    health_path = (payload.get("health") or "/health").strip()
    version = (payload.get("version") or "1.0").strip()

    item = {
        "name": name,
        "slug": slug,
        "service": _service_from_url(url, slug),
        "db_service": f"db_{slug}",
        "domain": "runtime_registered",
        "health_path": health_path,
        "url": url,
        "version": version,
    }
    _RUNTIME_MONOLITHS[slug] = item
    return item.copy()

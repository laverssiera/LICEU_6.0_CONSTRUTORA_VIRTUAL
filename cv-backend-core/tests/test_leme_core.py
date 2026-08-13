import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_leme_core.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gateway_registry_lists_15_monoliths():
    response = client.get("/gateway/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 15

    slugs = {item["slug"] for item in payload["monoliths"]}
    assert "core_os" in slugs
    assert "joh_brasileiro" in slugs


def test_gateway_registry_exposes_investor_relations_module_routes():
    response = client.get("/gateway/routes")

    assert response.status_code == 200
    payload = response.json()
    assert "modules" in payload
    assert "investor_relations" in payload["modules"]

    module_payload = payload["modules"]["investor_relations"]
    assert module_payload["prefix"] == "/gateway/investor-relations"
    assert "GET /gateway/investor-relations/routes" in module_payload["routes"]

    assert "quant_engine" in payload["modules"]
    quant_payload = payload["modules"]["quant_engine"]
    assert quant_payload["prefix"] == "/gateway/quant-engine"
    assert "POST /gateway/quant-engine/allocate" in quant_payload["routes"]

    assert "liceu_exchange" in payload["modules"]
    lex_payload = payload["modules"]["liceu_exchange"]
    assert lex_payload["prefix"] == "/gateway/lex"
    assert "POST /gateway/lex/orders" in lex_payload["routes"]

    assert "decision_intelligence" in payload["modules"]
    decision_payload = payload["modules"]["decision_intelligence"]
    assert decision_payload["prefix"] == "/gateway/decision-intelligence"
    assert "GET /gateway/decision-intelligence/system-state?portfolio=&project_id=" in decision_payload["routes"]

    assert "revenue_engine" in payload["modules"]
    revenue_payload = payload["modules"]["revenue_engine"]
    assert revenue_payload["prefix"] == "/gateway/revenue-engine"
    assert "POST /gateway/revenue-engine/leads/close-to-project" in revenue_payload["routes"]

    assert "execution_engine" in payload["modules"]
    execution_payload = payload["modules"]["execution_engine"]
    assert execution_payload["prefix"] == "/gateway/execution-engine"
    assert "POST /gateway/execution-engine/monitor/signal" in execution_payload["routes"]

    assert "capital_engine" in payload["modules"]
    capital_payload = payload["modules"]["capital_engine"]
    assert capital_payload["prefix"] == "/gateway/capital-engine"
    assert "POST /gateway/capital-engine/quant-lex/sync" in capital_payload["routes"]

    assert "trust_layer" in payload["modules"]
    trust_payload = payload["modules"]["trust_layer"]
    assert trust_payload["prefix"] == "/gateway/trust-layer"
    assert "POST /gateway/trust-layer/compliance/check" in trust_payload["routes"]

    assert "econotech" in payload["modules"]
    econotech_payload = payload["modules"]["econotech"]
    assert econotech_payload["prefix"] == "/gateway/econotech"
    assert "POST /gateway/econotech/analysis" in econotech_payload["routes"]
    assert "POST /gateway/econotech/stress/systemic" in econotech_payload["routes"]

    assert "earth_runtime" in payload["modules"]
    earth_payload = payload["modules"]["earth_runtime"]
    assert earth_payload["prefix"] == "/earth"
    assert "GET /earth/state/snapshot" in earth_payload["routes"]
    assert "GET /earth/routes" in earth_payload["routes"]


def test_global_health_exposes_network_dependencies():
    response = client.get("/health/global")

    assert response.status_code == 200
    payload = response.json()
    assert payload["network"] == "liceu-net"
    assert payload["total_pillars"] == 15
    assert "database" in payload["dependencies"]
    assert "redis" in payload["dependencies"]


def test_registry_services_lists_current_catalog():
    response = client.get("/registry/services")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["total"] >= 15
    assert any(item["slug"] == "core_os" for item in payload["services"])
    assert "modules" in payload
    assert "investor_relations" in payload["modules"]
    assert payload["modules"]["investor_relations"]["prefix"] == "/gateway/investor-relations"
    assert "quant_engine" in payload["modules"]
    assert payload["modules"]["quant_engine"]["prefix"] == "/gateway/quant-engine"
    assert "liceu_exchange" in payload["modules"]
    assert payload["modules"]["liceu_exchange"]["prefix"] == "/gateway/lex"
    assert "decision_intelligence" in payload["modules"]
    assert payload["modules"]["decision_intelligence"]["prefix"] == "/gateway/decision-intelligence"
    assert "revenue_engine" in payload["modules"]
    assert payload["modules"]["revenue_engine"]["prefix"] == "/gateway/revenue-engine"
    assert "execution_engine" in payload["modules"]
    assert payload["modules"]["execution_engine"]["prefix"] == "/gateway/execution-engine"
    assert "capital_engine" in payload["modules"]
    assert payload["modules"]["capital_engine"]["prefix"] == "/gateway/capital-engine"
    assert "trust_layer" in payload["modules"]
    assert payload["modules"]["trust_layer"]["prefix"] == "/gateway/trust-layer"
    assert "econotech" in payload["modules"]
    assert payload["modules"]["econotech"]["prefix"] == "/gateway/econotech"
    assert "earth_runtime" in payload["modules"]
    assert payload["modules"]["earth_runtime"]["prefix"] == "/earth"


def test_registry_register_adds_monolith_to_runtime_catalog():
    response = client.post(
        "/registry/register",
        json={
            "name": "cefeida_edge",
            "url": "http://cefeida-edge:8000",
            "health": "/health",
            "version": "1.0",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "registered"
    assert payload["monolith"]["slug"] == "cefeida_edge"

    routes = client.get("/gateway/routes")
    assert routes.status_code == 200
    slugs = {item["slug"] for item in routes.json()["monoliths"]}
    assert "cefeida_edge" in slugs


def test_registry_capabilities_describes_service_contract():
    response = client.get("/registry/capabilities/archimedes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "archimedes"
    assert payload["health_path"] == "/health"
    assert "gateway_proxy" in payload["routes"]
    assert "event_subscription" in payload["capabilities"]


def test_gateway_events_publishes_standardized_event():
    response = client.post(
        "/gateway/events",
        json={
            "event_id": "evt-001",
            "event_type": "obra.criada",
            "source": "archimedes",
            "version": "1.0",
            "timestamp": "2026-04-19T19:00:00Z",
            "correlation_id": "corr-001",
            "payload": {"obra_id": "OB-1"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "published"
    assert payload["event"]["event_type"] == "obra.criada"
    assert payload["event"]["correlation_id"] == "corr-001"


def test_events_subscribe_returns_service_channel_snapshot():
    client.post(
        "/gateway/events",
        json={
            "event_id": "evt-002",
            "event_type": "obra.atualizada",
            "source": "archimedes",
            "version": "1.0",
            "timestamp": "2026-04-20T10:00:00Z",
            "correlation_id": "corr-002",
            "payload": {"obra_id": "OB-2", "service": "archimedes"},
        },
    )

    response = client.get("/events/subscribe/archimedes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "subscribed"
    assert payload["service"] == "archimedes"
    assert "channel" in payload
    assert any(item["event_type"] == "obra.atualizada" for item in payload["events"])


def test_orchestrator_run_executes_service_flow():
    response = client.post(
        "/orchestrator/run",
        json={
            "service": "core_os",
            "action": "health_check",
            "mode": "proxy",
            "path": "/health",
            "payload": {"initiator": "john"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["service"] == "core_os"
    assert payload["mode"] == "proxy"
    assert "run_id" in payload
    assert "result" in payload


def test_gateway_query_returns_service_snapshot():
    response = client.post(
        "/gateway/query",
        json={
            "service": "core_os",
            "query": "health",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "core_os"
    assert "result" in payload


def test_gateway_proxy_can_reach_core_health():
    response = client.post(
        "/gateway/proxy/core_os",
        json={
            "method": "GET",
            "path": "/health",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"proxied", "simulated"}
    assert payload["service"] == "core_os"
    assert "result" in payload


def test_gateway_proxy_get_path_can_reach_core_health():
    response = client.get("/gateway/proxy/core_os/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "core_os"
    assert payload["result"]["status"] in {"healthy", "degraded"}


def test_gateway_proxy_post_path_accepts_payload():
    response = client.post(
        "/gateway/proxy/core_os/custom-action",
        json={"initiator": "john", "scope": "demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "core_os"
    assert payload["result"]["path"] == "/custom-action"
    assert payload["result"]["payload"]["initiator"] == "john"

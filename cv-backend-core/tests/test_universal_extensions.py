from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(tenant: str, role: str = "ADMIN") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


def _create_base_project(tenant: str = "tenant_liceu") -> str:
    response = client.post(
        "/universal/projects",
        json={
            "tenant": tenant,
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "project": "Projeto Extensao",
            "project_type": "PRJ",
            "year": 2026,
        },
        headers=_headers(tenant, "GESTOR"),
    )
    assert response.status_code == 200
    return response.json()["project"]["id"]



def test_universal_econotech_ingest_and_impact_adapter():
    project_id = _create_base_project("tenant_cliente_x")

    ingest_interest = client.post(
        "/universal/econotech/ingest",
        json={"tenant": "tenant_cliente_x", "source": "macro", "type": "interest_rate", "value": 12.5},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    ingest_inflation = client.post(
        "/universal/econotech/ingest",
        json={"tenant": "tenant_cliente_x", "source": "macro", "type": "inflation", "value": 6.2},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    ingest_demand = client.post(
        "/universal/econotech/ingest",
        json={"tenant": "tenant_cliente_x", "source": "market", "type": "demand", "value": 72},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )

    assert ingest_interest.status_code == 200
    assert ingest_inflation.status_code == 200
    assert ingest_demand.status_code == 200

    impact = client.post(
        "/universal/econotech/impact",
        json={"tenant": "tenant_cliente_x", "project_id": project_id, "scenario": "stress"},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    assert impact.status_code == 200
    payload = impact.json()
    assert payload["scenario"] == "stress"
    assert payload["recommended_action"] in {"pause", "adjust", "maintain", "accelerate"}



def test_universal_audit_recurrence_auto_actions_health_and_dashboard():
    tenant = "tenant_investidor_y"

    for _ in range(3):
        response = client.post(
            "/universal/audit/events",
            json={
                "tenant": tenant,
                "source": "workflow",
                "entity": "project:Z",
                "severity": "HIGH",
                "action": "validation_fail",
            },
            headers=_headers(tenant, "OPERADOR"),
        )
        assert response.status_code == 200

    third = response.json()["audit"]
    assert third["structural"] is True
    action_types = {item["type"] for item in third["automatic_actions"]}
    assert "task" in action_types
    assert "treinamento" in action_types
    assert "ajuste_de_processo" in action_types

    health = client.post(
        "/universal/health/score",
        json={"tenant": tenant, "finance": 58, "operational": 61, "risk": 55},
        headers=_headers(tenant, "OPERADOR"),
    )
    assert health.status_code == 200
    assert health.json()["status"] in {"critico", "atencao"}

    dashboard = client.get(f"/universal/dashboard?tenant={tenant}", headers=_headers(tenant, "INVESTIDOR"))
    assert dashboard.status_code == 200
    dash_payload = dashboard.json()
    assert "alerts" in dash_payload



def test_universal_john_and_knowledge_reuse():
    tenant = "tenant_liceu"

    score = client.post(
        "/universal/decision/score",
        json={
            "tenant": tenant,
            "retorno": 150,
            "risco": 35,
            "demanda": 100,
            "weights": {"retorno": 0.5, "risco": 0.3, "demanda": 0.2},
        },
        headers=_headers(tenant, "INVESTIDOR"),
    )
    assert score.status_code == 200

    john = client.post(
        "/universal/john/interpret",
        json={
            "tenant": tenant,
            "data": {"retorno": 150, "risco": 35, "demanda": 100},
            "scenario": "stability",
            "score": score.json()["score"],
        },
        headers=_headers(tenant, "JOHN"),
    )
    assert john.status_code == 200
    assert john.json()["mode"] in {"acelerar", "manter", "pausar"}
    assert "sugere" in john.json()["recommendation"].lower()

    recorded = client.post(
        "/universal/knowledge",
        json={
            "tenant": tenant,
            "input": {"segmento": "residencial", "regiao": "sudeste"},
            "resultado": {"decision": "APPROVED"},
            "licao": "segmento residencial no sudeste tende a acelerar",
        },
        headers=_headers(tenant, "JOHN"),
    )
    assert recorded.status_code == 200

    reused = client.post(
        "/universal/knowledge/reuse",
        json={
            "tenant": tenant,
            "input": {"segmento": "residencial", "regiao": "sudeste"},
            "limit": 3,
        },
        headers=_headers(tenant, "INVESTIDOR"),
    )
    assert reused.status_code == 200
    assert reused.json()["count"] >= 1

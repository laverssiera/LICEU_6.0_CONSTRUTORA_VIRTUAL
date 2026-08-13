from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(tenant: str = "tenant_liceu", role: str = "ADMIN") -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}


def test_universal_core_project_creation_and_mother_code():
    response = client.post(
        "/universal/projects",
        json={
            "tenant": "tenant_liceu",
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "project": "Projeto Alpha",
            "project_type": "PRJ",
            "year": 2026,
            "metadata": {
                "area": 980,
                "tipologia": "vertical",
                "unidades": 120,
                "custom_fields": {"zona": "leste"},
            },
        },
        headers=_headers("tenant_liceu", "ADMIN"),
    )

    assert response.status_code == 200
    payload = response.json()["project"]
    assert payload["pyramid"]["portfolio"] == "Obras Comuns"
    assert payload["pyramid"]["program"] == "Residencial"
    assert payload["pyramid"]["project"] == "Projeto Alpha"
    assert payload["mother_code"].startswith("OBR-RES-PRJ-2026-")
    assert payload["metadata"]["custom_fields"]["zona"] == "leste"



def test_universal_governance_dynamic_phases_rules_and_workflow():
    configured = client.post(
        "/universal/governance/phases",
        json={"phases": ["ideia", "viabilidade", "aprovacao", "execucao", "encerramento"]},
        headers=_headers("tenant_liceu", "GESTOR"),
    )
    assert configured.status_code == 200

    rule_added = client.post(
        "/universal/governance/rules",
        json={"fase": "viabilidade", "regra": "roi > 15%"},
        headers=_headers("tenant_liceu", "GESTOR"),
    )
    assert rule_added.status_code == 200

    created = client.post(
        "/universal/projects",
        json={
            "tenant": "tenant_cliente_x",
            "portfolio": "Corporate",
            "program": "Expansion",
            "project": "Linha Beta",
            "project_type": "PRJ",
            "year": 2026,
        },
        headers=_headers("tenant_cliente_x", "GESTOR"),
    )
    assert created.status_code == 200
    project_id = created.json()["project"]["id"]

    step_1 = client.post(
        "/universal/workflow/advance",
        json={"project_id": project_id, "tenant": "tenant_cliente_x", "metrics": {"roi": 12}},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    assert step_1.status_code == 200
    assert step_1.json()["status"] == "advanced"
    assert step_1.json()["phase"] == "viabilidade"

    blocked = client.post(
        "/universal/workflow/advance",
        json={"project_id": project_id, "tenant": "tenant_cliente_x", "metrics": {"roi": 12}},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "blocked"
    assert "roi > 15%" in blocked.json()["validation"]["failed"]

    approved = client.post(
        "/universal/workflow/advance",
        json={"project_id": project_id, "tenant": "tenant_cliente_x", "metrics": {"roi": 18}},
        headers=_headers("tenant_cliente_x", "OPERADOR"),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "advanced"
    assert approved.json()["phase"] == "aprovacao"
    assert approved.json()["event_type"] == "project.approved"



def test_universal_events_catalog_simulator_and_decision_score():
    catalog = client.get("/universal/events/catalog", headers=_headers("tenant_investidor_y", "INVESTIDOR"))
    assert catalog.status_code == 200
    event_names = catalog.json()["events"]
    assert "project.created" in event_names
    assert "project.approved" in event_names
    assert "project.started" in event_names
    assert "project.closed" in event_names

    simulated = client.post(
        "/universal/events/simulate",
        json={
            "tenant": "tenant_investidor_y",
            "event_types": ["project.created", "project.approved", "project.started", "project.closed"],
            "payload": {"project_id": "SIM-1"},
        },
        headers=_headers("tenant_investidor_y", "GESTOR"),
    )
    assert simulated.status_code == 200
    assert simulated.json()["count"] == 4

    score = client.post(
        "/universal/decision/score",
        json={
            "tenant": "tenant_investidor_y",
            "retorno": 180,
            "risco": 20,
            "demanda": 110,
            "weights": {"retorno": 0.5, "risco": 0.3, "demanda": 0.2},
        },
        headers=_headers("tenant_investidor_y", "INVESTIDOR"),
    )
    assert score.status_code == 200
    assert score.json()["decision"] == "APPROVED"
    assert score.json()["score"] >= 70

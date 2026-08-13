from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(tenant: str, role: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-Role": role}



def test_universal_requires_identity_headers():
    response = client.get("/universal/events/catalog")
    assert response.status_code == 401



def test_universal_blocks_role_without_permission():
    response = client.post(
        "/universal/governance/phases",
        json={"phases": ["ideia", "viabilidade", "aprovacao", "execucao", "encerramento"]},
        headers=_headers("tenant_cliente_x", "CLIENTE"),
    )
    assert response.status_code == 403



def test_universal_blocks_cross_tenant_resource_access_for_non_admin():
    created = client.post(
        "/universal/projects",
        json={
            "tenant": "tenant_cliente_x",
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "project": "Projeto Isolado",
            "project_type": "PRJ",
            "year": 2026,
        },
        headers=_headers("tenant_cliente_x", "GESTOR"),
    )
    assert created.status_code == 200
    project_id = created.json()["project"]["id"]

    blocked = client.get(
        f"/universal/projects/{project_id}",
        headers=_headers("tenant_investidor_y", "INVESTIDOR"),
    )
    assert blocked.status_code == 403

    admin_allowed = client.get(
        f"/universal/projects/{project_id}",
        headers=_headers("tenant_liceu", "ADMIN"),
    )
    assert admin_allowed.status_code == 200
    assert admin_allowed.json()["project"]["tenant"] == "tenant_cliente_x"

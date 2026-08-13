from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


client = TestClient(app)


def test_gateway_lex_routes_discovery_endpoint():
    response = client.get("/gateway/lex/routes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "liceu_exchange_gateway"
    assert "POST /gateway/lex/orders" in payload["routes"]
    assert "POST /gateway/lex/funds/subscribe" in payload["routes"]
    assert "POST /gateway/lex/indices/tokenize" in payload["routes"]
    assert "POST /gateway/lex/funds/tokenize" in payload["routes"]


def test_gateway_lex_health_forwards_payload(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://lex{path}",
            "http_status": 200,
            "result": {"status": "ok", "module": "liceu_exchange"},
        }

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.get("/gateway/lex/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "proxied"
    assert payload["result"]["module"] == "liceu_exchange"


def test_gateway_lex_fair_price_passes_query_params(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://lex{path}",
            "http_status": 200,
            "result": {"fair_price": 110.0, "market_price": 102.0, "john_recommendation": "comprar"},
        }

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.get("/gateway/lex/pricing/fair?roi=32&risk=0.4&progress=65")

    assert response.status_code == 200
    assert captured["params"] == {"roi": 32.0, "risk": 0.4, "progress": 65.0}


def test_gateway_lex_order_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://lex{path}",
            "http_status": 200,
            "result": {
                "investor_id": payload["investor_id"],
                "asset_id": payload["asset_id"],
                "type": payload["side"],
            },
        }

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.post(
        "/gateway/lex/orders",
        json={"investor_id": "I1", "asset_id": "A1", "side": "buy", "price": 105, "quantity": 100},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["investor_id"] == "I1"
    assert payload["result"]["asset_id"] == "A1"
    assert payload["result"]["type"] == "buy"


def test_gateway_lex_market_maker_passes_query(monkeypatch):
    captured = {"params": None}

    async def fake_request(method: str, path: str, payload=None, params=None):
        captured["params"] = params
        return {
            "status": "proxied",
            "target": f"mock://lex{path}",
            "http_status": 200,
            "result": {"bid": 99.0, "ask": 101.0},
        }

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.get("/gateway/lex/market-maker/A1?confidence=0.7")

    assert response.status_code == 200
    assert captured["params"] == {"confidence": 0.7}


def test_gateway_lex_market_maker_maintain_forwards_post(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        return {
            "status": "proxied",
            "target": f"mock://lex{path}",
            "http_status": 200,
            "result": {"orders_created": ["O1", "O2"]},
        }

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.post("/gateway/lex/market-maker/A1/maintain", json={"market_maker_id": "MMX", "confidence": 0.8})

    assert response.status_code == 200
    assert len(response.json()["result"]["orders_created"]) == 2


def test_gateway_lex_order_passes_through_403(monkeypatch):
    async def fake_request(method: str, path: str, payload=None, params=None):
        raise HTTPException(status_code=403, detail={"detail": "asset_not_tradable"})

    monkeypatch.setattr("app.api.endpoints.liceu_exchange_gateway._request_lex", fake_request)

    response = client.post(
        "/gateway/lex/orders",
        json={
            "investor_id": "I_BLOCK",
            "asset_id": "A_BLOCK",
            "side": "buy",
            "price": 100,
            "quantity": 10,
        },
    )

    assert response.status_code == 403

# Teste de falha: evento inválido e monolito offline
import pytest
import asyncio
# from liceu_6_0.core_sdk.sdk.event_bus import EventBus, validate_event

@pytest.mark.asyncio
async def test_evento_invalido_rejeitado():
    bus = EventBus()
    await bus.connect()
    # Payload inválido (faltando campo obrigatório)
    evento = {
        "type": "lead.created",
        "version": "v1",
        "payload": {"name": "Sem ID"},
        "source": "test",
        "correlation_id": "corr-fail"
    }
    errors = validate_event(evento)
    assert any("payload_invalido" in e or "schema_nao_encontrado" in e for e in errors)

@pytest.mark.asyncio
async def test_monolito_offline():
    # Simula tentativa de conexão ao NATS offline
    bus = EventBus(nats_url="nats://localhost:9999")
    with pytest.raises(Exception):
        await asyncio.wait_for(bus.connect(), timeout=2)

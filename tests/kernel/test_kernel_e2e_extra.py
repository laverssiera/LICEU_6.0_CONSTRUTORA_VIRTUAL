"""
Testes E2E adicionais para o Kernel LICEU 6.0
Cenários: evento inválido, escalonamento, drift alto (safety), execução bloqueada.
"""
import asyncio
import pytest
from unittest.mock import MagicMock

from backend.app.runtime.kernel.runtime_kernel import RuntimeKernel

@pytest.mark.asyncio
async def test_kernel_evento_invalido():
    event_bus = MagicMock()
    auditor = MagicMock()
    safety = MagicMock()
    router = MagicMock()
    validator = lambda event: False  # Evento sempre inválido
    kernel = RuntimeKernel(event_bus, validator, router, auditor, safety)
    event = {"type": "lead.created", "valid": False, "john": "john_crm", "action": "qualify_lead"}
    await kernel.handle_event(event)
    metrics = kernel.metrics_summary()
    assert metrics["blocked_decisions"] == 1
    auditor.log.assert_any_call(event, status="rejected", reason="invalid schema")

@pytest.mark.asyncio
async def test_kernel_escalonamento():
    event_bus = MagicMock()
    auditor = MagicMock()
    safety = MagicMock()
    router = MagicMock()
    validator = lambda event: True
    kernel = RuntimeKernel(event_bus, validator, router, auditor, safety)
    event = {"type": "lead.created", "valid": True, "john": "john_crm", "action": "qualify_lead", "escalation": True}
    await kernel.handle_event(event)
    metrics = kernel.metrics_summary()
    assert metrics["escalation_count"] == 1

@pytest.mark.asyncio
async def test_kernel_drift_alto_safety():
    event_bus = MagicMock()
    auditor = MagicMock()
    safety = MagicMock()
    safety.should_freeze.return_value = True
    router = MagicMock()
    validator = lambda event: True
    kernel = RuntimeKernel(event_bus, validator, router, auditor, safety)
    event = {"type": "lead.created", "valid": True, "john": "john_crm", "action": "qualify_lead"}
    await kernel.handle_event(event)
    metrics = kernel.metrics_summary()
    assert metrics["safety_triggers"] == 1
    auditor.log.assert_any_call(event, status="frozen", reason="drift alto")

@pytest.mark.asyncio
async def test_kernel_execucao_bloqueada():
    event_bus = MagicMock()
    auditor = MagicMock()
    safety = MagicMock()
    router = MagicMock()
    validator = lambda event: True
    # Simula bloqueio de governança
    from core_dna import autonomy_enforcement, governance_protection
    original = autonomy_enforcement.enforce_autonomy
    autonomy_enforcement.enforce_autonomy = MagicMock(side_effect=Exception("bloqueado"))
    kernel = RuntimeKernel(event_bus, validator, router, auditor, safety)
    event = {"type": "lead.created", "valid": True, "john": "john_crm", "action": "qualify_lead"}
    await kernel.handle_event(event)
    metrics = kernel.metrics_summary()
    assert metrics["blocked_decisions"] == 1
    auditor.log.assert_any_call(event, status="blocked", reason="bloqueado")
    autonomy_enforcement.enforce_autonomy = original

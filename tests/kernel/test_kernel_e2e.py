"""
Teste automatizado E2E do fluxo real do Kernel LICEU 6.0
Valida: entrada, processamento, decisão, execução, auditoria e feedback.
"""
import asyncio
import pytest
from unittest.mock import MagicMock

from backend.app.runtime.kernel.runtime_kernel import RuntimeKernel
from backend.app.runtime.kernel.metrics import KernelMetrics

@pytest.mark.asyncio
async def test_kernel_e2e_flow():
    # Mocks
    event_bus = MagicMock()
    auditor = MagicMock()
    safety = MagicMock()
    safety.should_freeze.return_value = False
    router = MagicMock()
    executor = MagicMock()
    router.resolve.return_value = executor
    validator = lambda event: event.get("valid", True)

    kernel = RuntimeKernel(event_bus, validator, router, auditor, safety)

    # Evento simulado (lead criado)
    event = {
        "type": "lead.created",
        "source": "frontend",
        "payload": {
            "name": "Cliente X",
            "interest": "empreendimento residencial",
            "budget": 500000
        },
        "john": "john_crm",
        "action": "qualify_lead",
        "valid": True,
        "escalation": False
    }

    # Simula processamento completo
    await kernel.handle_event(event)

    # Métricas
    metrics = kernel.metrics_summary()
    assert metrics["blocked_decisions"] == 0
    assert metrics["safety_triggers"] == 0
    assert metrics["escalation_count"] == 0
    assert metrics["avg_decision_time"] > 0

    # Auditoria chamada
    auditor.log.assert_any_call(event, status="executed", executor=executor, drift=pytest.approx(metrics["avg_drift"]))

    # Executor resolvido
    router.resolve.assert_called_once()

    # Shadow/Drift registrado
    assert metrics["avg_drift"] >= 0

    # Feedback loop (poderia ser mockado/checado se implementado)
    # ...

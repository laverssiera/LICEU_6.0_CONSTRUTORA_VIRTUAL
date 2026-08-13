import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SRC = ROOT / "liceu-core-schemas" / "src"
sys.path.insert(0, str(SCHEMA_SRC))

from liceu_core_schemas import (  # type: ignore
    BuildingBlock,
    BudgetEnvelope,
    CognitivePulse,
    LiceuToken,
    PulseSeverity,
    export_schema_registry,
)


def test_building_block_computes_total_cost():
    block = BuildingBlock(
        sku="KIT-001",
        name="Painel Estrutural",
        category="kit",
        unit="m2",
        quantity=Decimal("12"),
        unit_cost=Decimal("145.50"),
        supplier="fornecedor-alpha",
    )

    assert block.total_cost == Decimal("1746.00")
    assert block.currency == "BRL"


def test_budget_envelope_aggregates_building_blocks():
    block = BuildingBlock(
        sku="INS-002",
        name="Conector Metálico",
        category="insumo",
        unit="un",
        quantity=Decimal("50"),
        unit_cost=Decimal("8.00"),
    )

    envelope = BudgetEnvelope(
        budget_code="BGT-2026-001",
        project_code="OBRA-ALPHA",
        items=[block],
        contingency_rate=Decimal("0.10"),
        tax_rate=Decimal("0.05"),
    )

    assert envelope.subtotal == Decimal("400.00")
    assert envelope.total_estimate == Decimal("460.00")
    assert envelope.item_count == 1


def test_liceu_token_rejects_locked_balance_above_balance():
    with pytest.raises(ValueError):
        LiceuToken(
            wallet_id="wallet-1",
            holder_id="fornecedor-alpha",
            balance=Decimal("100.00"),
            locked_balance=Decimal("120.00"),
        )


def test_cognitive_pulse_and_schema_registry():
    pulse = CognitivePulse(
        pillar="joh_brasileiro",
        severity=PulseSeverity.CRITICAL,
        message="Fornecedor com divergência crítica no lote auditado.",
        recommended_action="Bloquear liberação até nova conferência.",
        tags=["qualidade", "compliance"],
    )

    registry = export_schema_registry()

    assert pulse.requires_ack is True
    assert "BuildingBlock" in registry
    assert "BudgetEnvelope" in registry
    assert "LiceuToken" in registry
    assert "CognitivePulse" in registry

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

MONEY_PLACES = Decimal("0.01")


def normalize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


class CurrencyCode(str, Enum):
    BRL = "BRL"


class PulseSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class BuildingBlock(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    sku: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=3, max_length=120)
    category: str = Field(description="Tipo do bloco: insumo, kit, modulo ou servico.")
    unit: str = Field(description="Unidade de medida operacional.")
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    currency: CurrencyCode = CurrencyCode.BRL
    supplier: str | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    weight_kg: Decimal | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        return normalize_money(self.quantity * self.unit_cost)


class BudgetEnvelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    budget_code: str = Field(min_length=3, max_length=64)
    project_code: str = Field(min_length=3, max_length=64)
    currency: CurrencyCode = CurrencyCode.BRL
    items: list[BuildingBlock] = Field(default_factory=list)
    contingency_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=1)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=1)
    status: str = Field(default="draft")
    approved_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item_currency(self) -> "BudgetEnvelope":
        invalid = [item.sku for item in self.items if item.currency != self.currency]
        if invalid:
            raise ValueError(f"Itens com moeda divergente no envelope: {', '.join(invalid)}")
        return self

    @computed_field
    @property
    def item_count(self) -> int:
        return len(self.items)

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return normalize_money(sum((item.total_cost for item in self.items), Decimal("0")))

    @computed_field
    @property
    def contingency_value(self) -> Decimal:
        return normalize_money(self.subtotal * self.contingency_rate)

    @computed_field
    @property
    def tax_value(self) -> Decimal:
        return normalize_money(self.subtotal * self.tax_rate)

    @computed_field
    @property
    def total_estimate(self) -> Decimal:
        return normalize_money(self.subtotal + self.contingency_value + self.tax_value)


class LiceuToken(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    wallet_id: str = Field(min_length=3, max_length=64)
    holder_id: str = Field(min_length=3, max_length=64)
    token_code: str = Field(default="LICEU", min_length=3, max_length=16)
    balance: Decimal = Field(ge=0)
    locked_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    exchange_rate_brl: Decimal = Field(default=Decimal("1.00"), gt=0)
    last_movement_type: str = Field(default="mint")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_balance(self) -> "LiceuToken":
        if self.locked_balance > self.balance:
            raise ValueError("Locked balance cannot exceed total balance")
        return self

    @computed_field
    @property
    def available_balance(self) -> Decimal:
        return normalize_money(self.balance - self.locked_balance)

    @computed_field
    @property
    def collateral_brl(self) -> Decimal:
        return normalize_money(self.balance * self.exchange_rate_brl)


class CognitivePulse(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    pulse_id: str = Field(default_factory=lambda: str(uuid4()))
    pillar: str = Field(min_length=3, max_length=64)
    severity: PulseSeverity = PulseSeverity.INFO
    message: str = Field(min_length=5, max_length=400)
    recommended_action: str | None = None
    sentiment_index: float = Field(default=0.0, ge=-1.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_ack: bool | None = None

    @model_validator(mode="after")
    def set_ack_default(self) -> "CognitivePulse":
        if self.requires_ack is None:
            self.requires_ack = self.severity == PulseSeverity.CRITICAL
        return self

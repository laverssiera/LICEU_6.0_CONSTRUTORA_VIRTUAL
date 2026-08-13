from __future__ import annotations

from typing import Any

from .models import BudgetEnvelope, BuildingBlock, CognitivePulse, LiceuToken


def export_schema_registry() -> dict[str, dict[str, Any]]:
    models = [BuildingBlock, BudgetEnvelope, LiceuToken, CognitivePulse]
    return {model.__name__: model.model_json_schema() for model in models}

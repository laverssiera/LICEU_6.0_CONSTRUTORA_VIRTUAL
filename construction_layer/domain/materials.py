from dataclasses import dataclass

@dataclass(frozen=True)
class Material:
    id: str
    name: str
    unit: str  # kg, m3, unidade
    cost_per_unit: float

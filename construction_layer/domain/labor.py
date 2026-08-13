from dataclasses import dataclass

@dataclass(frozen=True)
class Labor:
    id: str
    name: str
    cost_per_hour: float
    productivity_per_hour: float  # ex: m2 por hora

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Material:
    id: str
    name: str
    unit: str
    cost_per_unit: float

@dataclass
class Labor:
    id: str
    name: str
    productivity_per_hour: float  # ex: m2/h
    cost_per_hour: float

@dataclass
class Equipment:
    id: str
    name: str
    cost_per_hour: float

@dataclass
class ProductNode:
    id: str
    name: str
    unit: str
    quantity: float
    materials: List[Dict] = field(default_factory=list)
    labors: List[Dict] = field(default_factory=list)
    equipments: List[Dict] = field(default_factory=list)
    children: List["ProductNode"] = field(default_factory=list)

    def total_cost(self) -> float:
        total = 0
        for m in self.materials:
            total += m["material"].cost_per_unit * m["quantity"]
        for l in self.labors:
            hours = self.quantity / l["labor"].productivity_per_hour
            total += hours * l["labor"].cost_per_hour
        for e in self.equipments:
            total += e["equipment"].cost_per_hour * self.quantity
        for child in self.children:
            total += child.total_cost()
        return total

    def total_time(self) -> float:
        total = 0
        for l in self.labors:
            hours = self.quantity / l["labor"].productivity_per_hour
            total += hours
        for child in self.children:
            total += child.total_time()
        return total

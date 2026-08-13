from dataclasses import dataclass
from typing import List

@dataclass
class ProductComponent:
    type: str  # material | labor
    ref_id: str
    quantity: float

@dataclass
class Product:
    id: str
    name: str
    unit: str  # m2, m3
    components: List[ProductComponent]

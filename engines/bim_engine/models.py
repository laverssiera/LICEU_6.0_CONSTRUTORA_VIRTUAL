from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Geometry:
    type: str
    length: float = 0
    height: float = 0
    area: float = 0
    position: List[float] = field(default_factory=list)

@dataclass
class BIMElement:
    id: str
    type: str  # wall, slab, column
    geometry: Geometry
    metadata: Dict[str, Any] = field(default_factory=dict)

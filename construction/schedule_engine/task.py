from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    id: str
    name: str
    duration_days: float
    cost: float
    start_day: float = 0
    end_day: float = 0
    dependencies: List[str] = field(default_factory=list)

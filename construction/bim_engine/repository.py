from dataclasses import dataclass
from typing import Dict, List, Callable

@dataclass
class BIMTemplate:
    id: str
    name: str
    unit: str
    material_rules: List[Dict]
    labor_rules: List[Dict]
    equipment_rules: List[Dict]
    parameters: Dict
    validator: Callable = None

class BIMTemplateRepository:
    def __init__(self):
        self.templates = {}
    def add(self, template: BIMTemplate):
        self.templates[template.id] = template
    def get(self, template_id: str):
        return self.templates.get(template_id)

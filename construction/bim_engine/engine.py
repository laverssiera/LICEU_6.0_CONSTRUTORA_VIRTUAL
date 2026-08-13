from .repository import BIMTemplateRepository
from .mapper import BIMMapper
from construction_layer.domain.product_node import ProductNode

class BIMEngine:
    def __init__(self, material_repo, labor_repo, template_repo=None):
        self.material_repo = material_repo
        self.labor_repo = labor_repo
        self.template_repo = template_repo or BIMTemplateRepository()

    def generate_product_tree(self, template, quantity: float):
        materials = []
        labors = []
        # MATERIALIZAÇÃO
        for rule in template.material_rules:
            material = self.material_repo.get(rule["material_id"])
            materials.append({
                "material": material,
                "quantity": rule["factor"] * quantity
            })
        # MÃO DE OBRA
        for rule in template.labor_rules:
            labor = self.labor_repo.get(rule["labor_id"])
            labors.append({
                "labor": labor,
                "productivity_per_hour": rule["productivity"]
            })
        node = ProductNode(
            id=template.id,
            name=template.name,
            unit=template.unit,
            quantity=quantity,
            materials=materials,
            labors=labors
        )
        return node

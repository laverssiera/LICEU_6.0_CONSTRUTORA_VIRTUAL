from construction_layer.domain.materials import Material
from construction_layer.domain.labor import Labor
from construction_layer.domain.product import Product

class CostEngine:
    def __init__(self, materials: dict, labor: dict):
        self.materials = materials
        self.labor = labor

    def calculate(self, product: Product, quantity: float):
        total_cost = 0
        for component in product.components:
            if component.type == "material":
                material: Material = self.materials[component.ref_id]
                total_cost += material.cost_per_unit * component.quantity * quantity
            elif component.type == "labor":
                labor: Labor = self.labor[component.ref_id]
                hours_needed = quantity / labor.productivity_per_hour
                total_cost += hours_needed * labor.cost_per_hour
        return total_cost

from construction_layer.domain.labor import Labor
from construction_layer.domain.product import Product

class ExecutionEngine:
    def __init__(self, labor: dict):
        self.labor = labor

    def estimate_time(self, product: Product, quantity: float):
        total_hours = 0
        for component in product.components:
            if component.type == "labor":
                labor: Labor = self.labor[component.ref_id]
                hours = quantity / labor.productivity_per_hour
                total_hours += hours
        return total_hours

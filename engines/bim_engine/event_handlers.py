from engines.bim_engine.mapper import map_geometry_to_bim
from engines.bim_engine.product_tree import generate_product_tree

class BIMEventHandler:
    def handle(self, event):
        if event["type"] == "ui.wall.created":
            return self.process_wall(event)
    def process_wall(self, event):
        element = map_geometry_to_bim(event["payload"])
        product_tree = generate_product_tree(
            element,
            event["payload"]["config"]
        )
        return {
            "bim_element": element,
            "product_tree": product_tree
        }

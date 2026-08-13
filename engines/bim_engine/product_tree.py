from .rules import BLOCK_LIBRARY, FINISH_LIBRARY

def generate_product_tree(element, config):
    area = element.geometry.area
    block = config["block_type"]
    finish = config["finish"]
    block_rule = BLOCK_LIBRARY[block]
    finish_rule = FINISH_LIBRARY[finish]
    return {
        "element_id": element.id,
        "type": element.type,
        "inputs": [
            {
                "item": block,
                "quantity": area * block_rule["units_per_m2"],
                "unit": "unit"
            },
            {
                "item": "mortar",
                "quantity": area * block_rule["mortar_per_m2_kg"],
                "unit": "kg"
            },
            {
                "item": finish,
                "quantity": area,
                "unit": "m2"
            }
        ],
        "labor": {
            "hours": area * (block_rule["labor_hours_per_m2"] + finish_rule["labor_hours_per_m2"])
        },
        "cost_factor": block_rule["cost_factor"]
    }

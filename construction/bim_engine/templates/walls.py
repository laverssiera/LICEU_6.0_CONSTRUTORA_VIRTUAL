from construction.bim_engine.validators import validate_wall_params
from construction.bim_engine.repository import BIMTemplate

wall_template = BIMTemplate(
    id="wall.alvenaria.v1",
    name="Parede Alvenaria Vedação",
    unit="m2",
    material_rules=[
        {"material_id": "cimento", "factor": 5},
        {"material_id": "bloco", "factor": 12}
    ],
    labor_rules=[
        {"labor_id": "pedreiro", "productivity": 1.5}
    ],
    equipment_rules=[],
    parameters={
        "thickness": 0.14,
        "height": 2.7
    },
    validator=validate_wall_params
)

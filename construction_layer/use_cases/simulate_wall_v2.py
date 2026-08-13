from construction_layer.domain.product_node import Material, Labor, ProductNode

cimento = Material("mat_01", "Cimento", "kg", 0.8)
bloco = Material("mat_02", "Bloco 14x19x39", "un", 3.5)
pedreiro = Labor("lab_01", "Pedreiro", productivity_per_hour=1.5, cost_per_hour=25)

parede = ProductNode(
    id="wall_01",
    name="Parede Alvenaria",
    unit="m2",
    quantity=100,
    materials=[
        {"material": cimento, "quantity": 500},
        {"material": bloco, "quantity": 1200}
    ],
    labors=[
        {"labor": pedreiro}
    ]
)

print("Custo total:", parede.total_cost())
print("Tempo total:", parede.total_time())

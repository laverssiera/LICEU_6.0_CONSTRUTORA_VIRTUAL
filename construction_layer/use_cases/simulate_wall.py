from construction_layer.domain.materials import Material
from construction_layer.domain.labor import Labor
from construction_layer.services.cost_engine import CostEngine
from construction_layer.services.execution_engine import ExecutionEngine
from construction_layer.services.product_resolver import ProductResolver

# Base de dados mock (depois vem do banco)
materials = {
    "tijolo": Material(id="tijolo", name="Tijolo", unit="un", cost_per_unit=1.2),
    "argamassa": Material(id="argamassa", name="Argamassa", unit="m3", cost_per_unit=300),
}

labor = {
    "pedreiro": Labor(id="pedreiro", name="Pedreiro", cost_per_hour=25, productivity_per_hour=1.5),
}

# Resolver produto
product = ProductResolver.resolve("wall_alvenaria")

# Engines
cost_engine = CostEngine(materials, labor)
execution_engine = ExecutionEngine(labor)

# Simulação
area = 10  # m2

cost = cost_engine.calculate(product, area)
time = execution_engine.estimate_time(product, area)

print("Produto:", product.name)
print("Área:", area, "m2")
print("Custo estimado: R$", round(cost, 2))
print("Tempo estimado:", round(time, 2), "horas")

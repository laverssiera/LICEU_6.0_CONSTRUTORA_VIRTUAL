from .product import Product, ProductComponent

# Exemplo: parede de alvenaria
WALL_ALVENARIA = Product(
    id="wall_alvenaria",
    name="Parede de Alvenaria",
    unit="m2",
    components=[
        ProductComponent(type="material", ref_id="tijolo", quantity=25),
        ProductComponent(type="material", ref_id="argamassa", quantity=0.02),
        ProductComponent(type="labor", ref_id="pedreiro", quantity=1),
    ]
)

PRODUCT_TREE = {
    "wall_alvenaria": WALL_ALVENARIA
}

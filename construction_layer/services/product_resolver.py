from construction_layer.domain.product_tree import PRODUCT_TREE

class ProductResolver:
    @staticmethod
    def resolve(product_id: str):
        return PRODUCT_TREE.get(product_id)

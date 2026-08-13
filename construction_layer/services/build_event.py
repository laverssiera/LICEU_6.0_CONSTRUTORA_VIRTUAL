import json
from datetime import datetime
import uuid
from construction_layer.domain.product_node import ProductNode

def build_event(product_node: ProductNode):
    return {
        "id": str(uuid.uuid4()),
        "type": "construction.product.calculated",
        "version": "v1",
        "source": "construction_layer",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": json.dumps({
            "product_id": product_node.id,
            "name": product_node.name,
            "total_cost": product_node.total_cost(),
            "total_time": product_node.total_time()
        })
    }

from engines.bim_engine.models import BIMElement, Geometry

def map_geometry_to_bim(payload):
    geo = Geometry(
        type="wall",
        length=payload["length"],
        height=payload.get("height", 2.8),
        area=payload["length"] * payload.get("height", 2.8),
        position=payload.get("position", [0,0,0])
    )
    return BIMElement(
        id=payload["id"],
        type="wall",
        geometry=geo,
        metadata=payload.get("metadata", {})
    )

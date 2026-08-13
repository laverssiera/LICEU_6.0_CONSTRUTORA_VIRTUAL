import json
from datetime import datetime
import uuid

class InterplanetaryEventSchema:
    VALID_EVENTS = [
        "MISSION_CREATED",
        "TWIN_CREATED",
        "SATELLITE_INSPECTED",
        "MATERIAL_DISCOVERED",
        "HABITAT_SIMULATED",
        "NUCLEUS_SIMULATED"
    ]

    @staticmethod
    def generate_event(event_type, payload):
        if event_type not in InterplanetaryEventSchema.VALID_EVENTS:
            raise ValueError(f"Invalid Event Type. Must be one of {InterplanetaryEventSchema.VALID_EVENTS}")
        
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload,
            "schema_version": "1.0.interplanetary"
        }
        return event

if __name__ == "__main__":
    print("🛰️  Inicializando Interplanetary Event Schema...")
    events = [
        ("MISSION_CREATED", {"mission_name": "Missão Interplanetária Federada"}),
        ("TWIN_CREATED", {"twin_id": "digital-twin-interplanetary-001"}),
        ("SATELLITE_INSPECTED", {"satellite": "Orbitador Liceu-1", "status": "nominal"}),
        ("MATERIAL_DISCOVERED", {"material": "Estrutura Base", "quantity_kg": 25000}),
        ("HABITAT_SIMULATED", {"habitat": "Módulo Habitacional Alpha", "success_rate": 0.999}),
        ("NUCLEUS_SIMULATED", {"nucleus": "Núcleo Energético Ativo", "output_mw": 500})
    ]

    for e_type, payload in events:
        evt = InterplanetaryEventSchema.generate_event(e_type, payload)
        print(f"📡 Event Emitted: {json.dumps(evt, indent=2)}")

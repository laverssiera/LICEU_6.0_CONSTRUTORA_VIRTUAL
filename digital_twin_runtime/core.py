"""
Digital Twin Runtime Core
Representação viva do ecossistema em tempo real
"""

class DigitalTwinRuntime:
    def __init__(self):
        self.entities = {}
        self.events = []
        self.telemetry = {}

    def register_entity(self, entity_id, data):
        self.entities[entity_id] = data

    def emit_event(self, event):
        self.events.append(event)

    def update_telemetry(self, key, value):
        self.telemetry[key] = value

    def get_snapshot(self):
        return {
            "entities": self.entities,
            "events": self.events,
            "telemetry": self.telemetry
        }

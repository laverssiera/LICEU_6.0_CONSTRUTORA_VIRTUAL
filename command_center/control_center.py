"""
Ecosystem Command Center Core
- Dashboard operacional
- Telemetria em tempo real
- Monitoramento multi-monolito
"""

class CommandCenter:
    def __init__(self):
        self.layers = {}
        self.telemetry = {}

    def register_layer(self, name, data):
        self.layers[name] = data

    def update_telemetry(self, key, value):
        self.telemetry[key] = value

    def get_dashboard(self):
        return {
            "layers": self.layers,
            "telemetry": self.telemetry
        }

"""
Governance Center Core
Central operacional holográfica do LICEU 6.0
"""

class GovernanceCenter:
    def __init__(self):
        self.dashboards = {}
        self.heatmaps = {}
        self.alerts = []

    def add_dashboard(self, name, data):
        self.dashboards[name] = data

    def add_heatmap(self, name, data):
        self.heatmaps[name] = data

    def send_alert(self, alert):
        self.alerts.append(alert)

    def get_status(self):
        return {
            "dashboards": self.dashboards,
            "heatmaps": self.heatmaps,
            "alerts": self.alerts
        }

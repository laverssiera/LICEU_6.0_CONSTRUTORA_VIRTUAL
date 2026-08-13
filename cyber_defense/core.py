"""
Cyber Defense Core
Defesa operacional do ecossistema
"""

class CyberDefense:
    def __init__(self):
        self.threats = []
        self.incidents = []

    def detect_threat(self, event):
        if "malware" in event.get("tags", []):
            self.threats.append(event)
            return True
        return False

    def report_incident(self, incident):
        self.incidents.append(incident)

    def get_status(self):
        return {
            "threats": self.threats,
            "incidents": self.incidents
        }

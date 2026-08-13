"""
Threat Intelligence Core
Inteligência de ameaças e análise comportamental
"""

class ThreatIntelligence:
    def __init__(self):
        self.anomalies = []
        self.patterns = []

    def detect_anomaly(self, data):
        if data.get("score", 0) > 0.8:
            self.anomalies.append(data)
            return True
        return False

    def add_pattern(self, pattern):
        self.patterns.append(pattern)

    def get_status(self):
        return {
            "anomalies": self.anomalies,
            "patterns": self.patterns
        }

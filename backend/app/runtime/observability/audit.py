from datetime import datetime

class AuditTrail:

    def __init__(self):
        self.logs = []

    def record(self, action: str, payload: dict):

        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "payload": payload
        })

import time
from collections import defaultdict

class KernelMetrics:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.blocked_decisions = 0
        self.safety_triggers = 0
        self.escalation_count = 0
        self.drift_scores = []

    def record_decision_time(self, start, end):
        self.metrics['decision_time'].append(end - start)

    def record_escalation(self):
        self.escalation_count += 1

    def record_drift(self, drift):
        self.drift_scores.append(drift)

    def record_blocked(self):
        self.blocked_decisions += 1

    def record_safety(self):
        self.safety_triggers += 1

    def summary(self):
        return {
            'avg_decision_time': sum(self.metrics['decision_time']) / len(self.metrics['decision_time']) if self.metrics['decision_time'] else 0,
            'escalation_count': self.escalation_count,
            'avg_drift': sum(self.drift_scores) / len(self.drift_scores) if self.drift_scores else 0,
            'blocked_decisions': self.blocked_decisions,
            'safety_triggers': self.safety_triggers
        }

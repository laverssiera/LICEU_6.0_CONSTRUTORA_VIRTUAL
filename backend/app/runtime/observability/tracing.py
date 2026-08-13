class Tracing:
    def __init__(self):
        self.traces = []

    def trace(self, operation: str, context: dict):
        self.traces.append({"operation": operation, "context": context})

    def get_traces(self):
        return self.traces

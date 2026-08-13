# Mock de observabilidade soberana
class ObservabilityMock:
    def trace(self, event, context=None):
        return f"TRACE: {event}"

class Metrics:

    def __init__(self):
        self.data = {}

    def increment(self, metric: str):
        self.data[metric] = self.data.get(metric, 0) + 1

    def get(self):
        return self.data

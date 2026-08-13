class BIMRegistry:
    def __init__(self):
        self.engine = None
    def register(self, engine):
        self.engine = engine
    def execute(self, event):
        if not self.engine:
            raise Exception("BIM Engine not registered in LICEU Runtime")
        return self.engine.process_event(event)

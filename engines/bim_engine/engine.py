from engines.bim_engine.event_handlers import BIMEventHandler

class BIMEngine:
    def __init__(self):
        self.handler = BIMEventHandler()
    def process_event(self, event):
        return self.handler.handle(event)

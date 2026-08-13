# Script de replay de eventos usando o pipeline
from monolito.event_store import replay_events
from monolito.event_middleware import process_event

if __name__ == "__main__":
    print("Replaying all events via pipeline...")
    replay_events(process_event)

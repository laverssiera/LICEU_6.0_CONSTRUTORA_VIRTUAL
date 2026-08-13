from app.internal import event_bus


def _reset_fallback_bus_state() -> None:
    event_bus._fallback_bus.messages = []
    event_bus._fallback_bus.subscribers = {}


def test_get_event_bus_falls_back_when_nats_client_is_unavailable(monkeypatch):
    _reset_fallback_bus_state()
    monkeypatch.setattr(event_bus.settings, "EVENT_BUS_PROVIDER", "nats")
    monkeypatch.setattr(event_bus, "NATS", None)

    bus = event_bus.get_event_bus()

    assert bus.provider == "memory"


def test_nats_event_bus_publish_notifies_base_subscribers(monkeypatch):
    _reset_fallback_bus_state()
    monkeypatch.setattr(event_bus.settings, "EVENT_BUS_PROVIDER", "nats")
    monkeypatch.setattr(event_bus.settings, "NATS_URL", "nats://mock:4222")

    class FakeNatsClient:
        def __init__(self) -> None:
            self.is_connected = False
            self.published = []

        async def connect(self, *_args, **_kwargs):
            self.is_connected = True

        async def publish(self, channel: str, payload: bytes):
            self.published.append((channel, payload))

    monkeypatch.setattr(event_bus, "NATS", FakeNatsClient)

    bus = event_bus.get_event_bus()
    received = []

    def _handler(entry):
        received.append(entry)

    bus.subscribe("strategy.created", _handler)
    result = bus.publish("strategy.created", {"strategy_id": 123})

    assert bus.provider == "nats"
    assert result.provider == "nats"
    assert result.channel == "strategy.created"
    assert result.delivered is True
    assert received
    assert received[0]["channel"] == "strategy.created"
    assert received[0]["event"]["strategy_id"] == 123

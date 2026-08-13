from __future__ import annotations

import json
import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from app.config import settings

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

try:
    from nats.aio.client import Client as NATS
except Exception:  # pragma: no cover
    NATS = None


@dataclass
class PublishResult:
    provider: str
    channel: str
    delivered: bool
    message: Dict[str, Any]


class InMemoryEventBus:
    provider = "memory"

    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def ping(self) -> bool:
        return True

    def publish(self, channel: str, message: Dict[str, Any]) -> PublishResult:
        entry = {"channel": channel, "message": message}
        self.messages.append(entry)
        self._notify(channel, message)
        return PublishResult(
            provider=self.provider,
            channel=channel,
            delivered=True,
            message=message,
        )

    def recent_messages(self, channel: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        items = self.messages
        if channel:
            items = [entry for entry in items if entry.get("channel") == channel]
        return items[-limit:]

    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        self.subscribers.setdefault(channel, []).append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        callbacks = self.subscribers.get(channel, [])
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks and channel in self.subscribers:
            self.subscribers.pop(channel, None)

    def _notify(self, channel: str, message: Dict[str, Any]) -> None:
        callbacks = [*self.subscribers.get(channel, []), *self.subscribers.get("*", [])]
        payload = {"channel": channel, "event": message}
        for callback in callbacks:
            try:
                callback(payload)
            except Exception:
                continue


class RedisEventBus:
    provider = "redis"

    def __init__(self, url: str) -> None:
        if redis is None:
            raise RuntimeError("Redis client not available")
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self.client.ping())

    def publish(self, channel: str, message: Dict[str, Any]) -> PublishResult:
        self.client.publish(channel, json.dumps(message, ensure_ascii=False))
        _fallback_bus.publish(channel, message)
        return PublishResult(
            provider=self.provider,
            channel=channel,
            delivered=True,
            message=message,
        )

    def recent_messages(self, channel: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        return _fallback_bus.recent_messages(channel=channel, limit=limit)

    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        _fallback_bus.subscribe(channel, callback)

    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        _fallback_bus.unsubscribe(channel, callback)


class NatsEventBus:
    provider = "nats"

    def __init__(self, url: str) -> None:
        if NATS is None:
            raise RuntimeError("NATS client not available")
        self.url = url
        self.client = NATS()

    async def _connect(self) -> None:
        if not self.client.is_connected:
            await self.client.connect(
                self.url,
                connect_timeout=settings.NATS_CONNECT_TIMEOUT_SECONDS,
            )

    def _run_async(self, coro: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coro)
            return

        loop.create_task(coro)

    def ping(self) -> bool:
        try:
            self._run_async(self._connect())
            return True
        except Exception:
            return False

    def publish(self, channel: str, message: Dict[str, Any]) -> PublishResult:
        async def _publish() -> None:
            await self._connect()
            await self.client.publish(channel, json.dumps(message, ensure_ascii=False).encode())

        delivered = True
        try:
            self._run_async(_publish())
        except Exception:
            delivered = False

        # Subscriber base local para manter comportamento consistente com os demais providers.
        _fallback_bus.publish(channel, message)
        return PublishResult(
            provider=self.provider,
            channel=channel,
            delivered=delivered,
            message=message,
        )

    def recent_messages(self, channel: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        return _fallback_bus.recent_messages(channel=channel, limit=limit)

    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        _fallback_bus.subscribe(channel, callback)

    def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        _fallback_bus.unsubscribe(channel, callback)


_fallback_bus = InMemoryEventBus()


def get_event_bus() -> RedisEventBus | InMemoryEventBus:
    provider = (settings.EVENT_BUS_PROVIDER or "").strip().lower()

    if provider == "nats":
        if settings.NATS_URL and NATS is not None:
            try:
                bus = NatsEventBus(settings.NATS_URL)
                bus.ping()
                return bus
            except Exception:
                return _fallback_bus
        return _fallback_bus

    if settings.REDIS_URL and redis is not None:
        try:
            bus = RedisEventBus(settings.REDIS_URL)
            bus.ping()
            return bus
        except Exception:
            return _fallback_bus
    return _fallback_bus

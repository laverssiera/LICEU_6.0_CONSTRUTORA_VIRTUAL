from __future__ import annotations

import json
from typing import Any

from app.config import settings

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class InMemoryShortTermMemory:
    provider = "memory"

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def set_context(self, key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
        self.store[key] = value

    def get_context(self, key: str) -> dict[str, Any]:
        return self.store.get(key, {})


class RedisShortTermMemory:
    provider = "redis"

    def __init__(self, url: str) -> None:
        if redis is None:
            raise RuntimeError("Redis client unavailable")
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def set_context(self, key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
        self.client.setex(f"john:memory:{key}", ttl_seconds, json.dumps(value, ensure_ascii=False))

    def get_context(self, key: str) -> dict[str, Any]:
        raw = self.client.get(f"john:memory:{key}")
        return json.loads(raw) if raw else {}


_fallback = InMemoryShortTermMemory()


def get_short_term_memory() -> RedisShortTermMemory | InMemoryShortTermMemory:
    if settings.REDIS_URL and redis is not None:
        try:
            memory = RedisShortTermMemory(settings.REDIS_URL)
            memory.client.ping()
            return memory
        except Exception:
            return _fallback
    return _fallback

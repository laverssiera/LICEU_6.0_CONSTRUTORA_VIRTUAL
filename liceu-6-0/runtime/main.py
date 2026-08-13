import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.append("/shared/core-sdk")

from redis.asyncio import Redis
from sdk.event_bus import EventBus

REGISTRY_PATH = Path(os.getenv("EVENT_REGISTRY_PATH", "/event-registry/events.json"))
EVENT_LOG_PATH = Path(os.getenv("RUNTIME_EVENT_LOG_PATH", "/app/data/events.jsonl"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RUNTIME_STREAM = os.getenv("RUNTIME_EVENT_STREAM", "liceu.runtime.events")
DEAD_LETTER_STREAM = os.getenv("RUNTIME_DEAD_LETTER_STREAM", "liceu.runtime.dead_letters")
RETRY_STREAM = os.getenv("RUNTIME_RETRY_STREAM", "liceu.runtime.retries")
MAX_PERSIST_RETRIES = int(os.getenv("RUNTIME_MAX_PERSIST_RETRIES", "3"))
PERSIST_RETRY_DELAY_SECONDS = float(os.getenv("RUNTIME_PERSIST_RETRY_DELAY_SECONDS", "0.25"))


def load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}

    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def append_history(event: dict) -> None:
    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=True) + "\n")


def append_dead_letter(record: dict[str, Any]) -> None:
    dead_letter_path = EVENT_LOG_PATH.parent / "dead_letters.jsonl"
    dead_letter_path.parent.mkdir(parents=True, exist_ok=True)
    with dead_letter_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=True) + "\n")


def route_snapshot(event: dict, registry: dict[str, dict]) -> dict[str, object]:
    event_type = event.get("type", "unknown")
    spec = registry.get(event_type, {})
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "source": event.get("source", "unknown"),
        "expected_consumers": spec.get("consumers", []),
        "registry_version": spec.get("current_version"),
    }


async def persist_runtime_record(stream_name: str, record: dict[str, Any]) -> None:
    redis_client = handler.redis
    serialized = {key: json.dumps(value, ensure_ascii=True) for key, value in record.items()}
    await redis_client.xadd(stream_name, serialized, maxlen=1000, approximate=True)


async def persist_with_retry(stream_name: str, record: dict[str, Any]) -> None:
    last_error: Exception | None = None

    for attempt in range(1, MAX_PERSIST_RETRIES + 1):
        try:
            await persist_runtime_record(stream_name, record)
            if attempt > 1:
                print(f"[runtime] persistencia recuperada em {stream_name} na tentativa {attempt}", flush=True)
            return
        except Exception as exc:
            last_error = exc
            print(f"[runtime] falha ao persistir em {stream_name} tentativa {attempt}: {exc}", flush=True)
            if attempt < MAX_PERSIST_RETRIES:
                await asyncio.sleep(PERSIST_RETRY_DELAY_SECONDS * attempt)

    retry_record = {
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "stream_name": stream_name,
        "record": record,
        "error": str(last_error) if last_error is not None else "unknown",
    }
    await persist_runtime_record(RETRY_STREAM, retry_record)
    raise RuntimeError(f"Persistencia falhou para {stream_name} apos {MAX_PERSIST_RETRIES} tentativas")


async def dead_letter_event(event: dict[str, Any], reason: str) -> None:
    dead_letter_record = {
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "event": event,
    }
    append_dead_letter(dead_letter_record)
    await persist_with_retry(DEAD_LETTER_STREAM, dead_letter_record)


async def handler(event: dict) -> None:
    append_history(event)

    snapshot = route_snapshot(event, handler.registry)
    await persist_with_retry(
        RUNTIME_STREAM,
        {
            "recorded_at": snapshot["recorded_at"],
            "event": event,
            "route_snapshot": snapshot,
        },
    )
    print(f"[runtime] evento recebido: {event}", flush=True)
    print(f"[runtime] rota prevista: {snapshot}", flush=True)


async def invalid_handler(event: dict[str, Any], errors: list[str]) -> None:
    await dead_letter_event(event, ";".join(errors))
    print(f"[runtime] evento descartado para dead-letter: {errors}", flush=True)


async def main() -> None:
    bus = EventBus(nats_url=os.getenv("NATS_URL", "nats://nats:4222"))
    handler.redis = Redis.from_url(REDIS_URL, decode_responses=True)
    handler.registry = load_registry()
    try:
        await bus.run_forever(handler, invalid_handler=invalid_handler)
    finally:
        await handler.redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())

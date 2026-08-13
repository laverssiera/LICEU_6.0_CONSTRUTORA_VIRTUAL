import asyncio
import json
import os

from nats.aio.client import Client as NATS
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")
NATS_URL = os.getenv("NATS_PUBLIC_URL", "nats://localhost:4222")
DEAD_LETTER_STREAM = os.getenv("RUNTIME_DEAD_LETTER_STREAM", "liceu.runtime.dead_letters")
REPLAY_STREAM = os.getenv("RUNTIME_REPLAY_STREAM", "liceu.runtime.replays")


async def main() -> None:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    nats_client = NATS()
    await nats_client.connect(NATS_URL)

    replayed = 0
    entries = await redis_client.xrange(DEAD_LETTER_STREAM, count=100)

    for entry_id, fields in entries:
        raw_event = fields.get("event")
        if raw_event is None:
            continue

        event = json.loads(raw_event)
        if "version" not in event:
            event["version"] = "v1"

        await nats_client.publish("liceu.events", json.dumps(event).encode())
        await redis_client.xadd(
            REPLAY_STREAM,
            {
                "replayed_at": json.dumps(asyncio.get_running_loop().time()),
                "source_entry": json.dumps(entry_id),
                "event": json.dumps(event, ensure_ascii=True),
            },
            maxlen=1000,
            approximate=True,
        )
        replayed += 1

    print(f"replayed={replayed}")

    await nats_client.close()
    await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import json
import os
from datetime import datetime, timezone

from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


async def main() -> None:
    nc = NATS()
    await nc.connect(NATS_URL)

    async def on_message(msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"[RUNTIME] {subject}: {data}", flush=True)

    await nc.subscribe("liceu.events", cb=on_message)

    boot_payload = {
        "type": "system.boot",
        "version": "v1",
        "source": "runtime",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await nc.publish("liceu.events", json.dumps(boot_payload).encode())
    print(f"[RUNTIME] conectado em {NATS_URL} e aguardando eventos em liceu.events...", flush=True)

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())

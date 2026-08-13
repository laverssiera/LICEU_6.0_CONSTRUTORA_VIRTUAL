import asyncio
import json
import os

from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


async def main() -> None:
    nc = NATS()
    await nc.connect(NATS_URL)

    async def handle_contract(msg):
        try:
            event = json.loads(msg.data.decode())
        except Exception:
            event = {"raw": msg.data.decode()}

        if event.get("type") in {"contract.created", "lead.created"}:
            print("JURIDICO RECEBEU:", event, flush=True)

    await nc.subscribe("liceu.events", cb=handle_contract)

    print(f"[JURIDICOTECH] ouvindo em {NATS_URL}: liceu.events", flush=True)

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())

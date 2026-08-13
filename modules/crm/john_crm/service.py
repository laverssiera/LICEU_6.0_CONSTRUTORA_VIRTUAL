import asyncio
import json
import os
import signal
import sys
import time
from pathlib import Path

from nats.aio.client import Client as NATS

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from john_crm import JohnCRM

HEALTH_FILE = Path("/tmp/john_crm_healthy")
RUNNING = True


class NatsBus:
    def __init__(self, client: NATS):
        self.client = client

    async def publish(self, subject: str, payload: dict):
        await self.client.publish(subject, json.dumps(payload).encode("utf-8"))


def _handle_stop(*_args):
    global RUNNING
    RUNNING = False


async def main() -> None:
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    heartbeat_subject = os.getenv("EVENT_SUBJECT", "crm.lead.created")
    source = os.getenv("JOHN_SOURCE", "site")

    nc = NATS()
    await nc.connect(nats_url)
    john = JohnCRM(nats_bus=NatsBus(nc))

    print(f"[JOHN-CRM] service iniciado em {nats_url}", flush=True)

    while RUNNING:
        # Marca de healthcheck simples para o Docker validar se o loop segue ativo.
        HEALTH_FILE.write_text(str(int(time.time())), encoding="utf-8")

        heartbeat_payload = {
            "type": "crm.heartbeat",
            "source": "john_crm",
            "ts": int(time.time()),
        }
        await nc.publish(heartbeat_subject, json.dumps(heartbeat_payload).encode("utf-8"))

        await john.chat(
            "Quero construir 20 casas",
            context={"source": source, "name": "system-heartbeat", "email": "system@liceu.local"},
        )
        await asyncio.sleep(30)

    await nc.drain()
    print("[JOHN-CRM] service finalizado", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

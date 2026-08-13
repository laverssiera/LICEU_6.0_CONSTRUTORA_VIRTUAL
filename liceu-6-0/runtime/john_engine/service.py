import asyncio
import json
import os
import signal
import time
from pathlib import Path

import httpx
from nats.aio.client import Client as NATS

from john_engine import JohnInternal

HEALTH_FILE = Path("/tmp/john_engine_healthy")
RUNNING = True


def _handle_stop(*_args):
    global RUNNING
    RUNNING = False


async def main() -> None:
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    john = JohnInternal()
    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    subscribe_subject = os.getenv("EVENT_SUBJECT", "liceu.events")
    output_subject = os.getenv("JOHN_OUTPUT_SUBJECT", "john.interpreted")
    backend_ingest_url = os.getenv("BACKEND_INGEST_URL", "http://backend:8000/john/interpreted/ingest")
    internal_token = os.getenv("JOHN_INTERNAL_TOKEN", "john-internal-dev")

    nc = NATS()
    await nc.connect(nats_url)

    async def _handle(msg):
        raw = msg.data.decode("utf-8")
        try:
            event = json.loads(raw)
        except Exception:
            event = {"type": "unknown", "raw": raw}

        result = await john.interpret(event)
        interpretation = {
            "type": "john.interpreted",
            "source": "john_engine",
            "input_subject": msg.subject,
            "input_event": event,
            "result": result,
            "ts": int(time.time()),
        }
        await nc.publish(output_subject, json.dumps(interpretation).encode("utf-8"))

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(
                    backend_ingest_url,
                    headers={"x-john-internal-token": internal_token},
                    json=interpretation,
                )
        except Exception as exc:
            print(f"[JOHN-ENGINE] backend ingest falhou: {exc}", flush=True)

        print(f"[JOHN-ENGINE] interpreted: {result['action']} from {msg.subject}", flush=True)

    await nc.subscribe(subscribe_subject, cb=_handle)

    print(f"[JOHN-ENGINE] service iniciado em {nats_url}, ouvindo {subscribe_subject}", flush=True)

    while RUNNING:
        HEALTH_FILE.write_text(str(int(time.time())), encoding="utf-8")
        await asyncio.sleep(30)

    await nc.drain()
    print("[JOHN-ENGINE] service finalizado", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

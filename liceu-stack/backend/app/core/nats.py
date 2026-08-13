import json

from nats.aio.client import Client as NATS

from app.core.config import NATS_URL

nc = NATS()


async def connect_nats() -> None:
    if not nc.is_connected:
        await nc.connect(NATS_URL)


async def publish(subject: str, payload: dict) -> None:
    if not nc.is_connected:
        await connect_nats()
    await nc.publish(subject, json.dumps(payload).encode())

# Criação dos streams JetStream para LICEU
# Execute este script após subir o NATS com JetStream habilitado

import asyncio
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, RetentionPolicy

STREAMS = [
    {
        "name": "LICEU_EVENTS",
        "subjects": ["liceu.events.*"],
        "retention": RetentionPolicy.Limits,
        "max_msgs": 100000,
        "max_bytes": 1_000_000_000,  # 1GB
        "max_age": 86400 * 7,  # 7 dias
    },
    {
        "name": "LICEU_AUDIT",
        "subjects": ["liceu.audit.*"],
        "retention": RetentionPolicy.Limits,
        "max_msgs": 100000,
        "max_bytes": 1_000_000_000,
        "max_age": 86400 * 30,  # 30 dias
    },
    {
        "name": "LICEU_DLQ",
        "subjects": ["liceu.dlq.*"],
        "retention": RetentionPolicy.Limits,
        "max_msgs": 100000,
        "max_bytes": 1_000_000_000,
        "max_age": 86400 * 30,
    },
]

async def main():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    js = nc.jetstream()
    for stream in STREAMS:
        cfg = StreamConfig(
            name=stream["name"],
            subjects=stream["subjects"],
            retention=stream["retention"],
            max_msgs=stream["max_msgs"],
            max_bytes=stream["max_bytes"],
            max_age=stream["max_age"],
        )
        try:
            await js.add_stream(cfg)
            print(f"[OK] Stream criado: {stream['name']}")
        except Exception as e:
            print(f"[WARN] {stream['name']}: {e}")
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())

# Criação de consumers duráveis por monolito
# Execute após os streams existirem

import asyncio
from nats.aio.client import Client as NATS

MONOLITOS = [
    "monolito",
    "monolito_exemplo",
    # Adicione outros nomes de monolitos conforme necessário
]

STREAM = "LICEU_EVENTS"
SUBJECT = "liceu.events.*"

async def main():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    js = nc.jetstream()
    for monolito in MONOLITOS:
        durable = f"{monolito}_consumer"
        try:
            await js.add_consumer(
                STREAM,
                {
                    "durable_name": durable,
                    "filter_subject": SUBJECT,
                    "ack_policy": "explicit"
                }
            )
            print(f"[OK] Consumer criado: {durable}")
        except Exception as e:
            print(f"[WARN] {durable}: {e}")
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())

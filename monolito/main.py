# Startup padronizado do monolito
from monolito.config import NATS_URL
from liceu-6.0.core-sdk.sdk.event_bus import EventBus
import multiprocessing
import asyncio
import signal
import sys

def start_healthcheck():
    from monolito.healthcheck import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()
    print("Monolito iniciado e conectado ao EventBus!")
    # Timeout padrão: encerra após 5 minutos sem atividade
    def timeout_handler(signum, frame):
        print("[main] Timeout padrão atingido. Encerrando.")
        sys.exit(1)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutos
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    p = multiprocessing.Process(target=start_healthcheck)
    p.start()
    asyncio.run(main())
    p.join()

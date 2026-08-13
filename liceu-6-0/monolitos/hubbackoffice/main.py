from fastapi import FastAPI
from metrics_config import MetricsMiddleware, metrics_endpoint
app = FastAPI()
app.add_middleware(MetricsMiddleware)
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
sys.path.append("/shared/core-sdk")
import asyncio
import os
import sys
sys.path.append("/shared/core-sdk")
from sdk.event_bus import EventBus
# Logging estruturado e correlation ID
from logging_config import setup_logging, get_correlation_id, set_correlation_id
import logging

setup_logging()
logger = logging.getLogger("hubbackoffice")

async def handler(event: dict) -> None:
    bus = handler.bus
    event_type = event.get("type")
    payload = event.get("payload", {})
    correlation_id = event.get("correlation_id") or get_correlation_id()
    set_correlation_id(correlation_id)
    logger.info(f"Evento recebido: {event_type}", extra={"correlation_id": correlation_id})

    if event_type == "contract.signed":
        await bus.publish("payment.generated", payload, source="hubbackoffice")
        logger.info("Pagamento gerado", extra={"correlation_id": correlation_id})

    if event_type == "payment.generated":
        logger.info("Financeiro registrou pagamento", extra={"correlation_id": correlation_id})
        print("Financeiro registrou pagamento", payload, flush=True)

async def main() -> None:
    bus = EventBus(nats_url=os.getenv("NATS_URL", "nats://nats:4222"))
    handler.bus = bus
    await bus.run_forever(handler)

if __name__ == "__main__":
    asyncio.run(main())

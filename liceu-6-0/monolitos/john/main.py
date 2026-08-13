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
logger = logging.getLogger("john")

async def handler(event: dict) -> None:
    event_type = event.get("type")
    correlation_id = event.get("correlation_id") or get_correlation_id()
    set_correlation_id(correlation_id)
    logger.info(f"Evento recebido: {event_type}", extra={"correlation_id": correlation_id})

    if event_type == "lead.created":
        logger.info("John sugere abordagem", extra={"correlation_id": correlation_id})
        print("John sugere abordagem", event.get("payload", {}), flush=True)

    if event_type == "deal.lost":
        logger.info("John aprende padrao de perda", extra={"correlation_id": correlation_id})
        print("John aprende padrao de perda", event.get("payload", {}), flush=True)

async def main() -> None:
    bus = EventBus(nats_url=os.getenv("NATS_URL", "nats://nats:4222"))
    await bus.run_forever(handler)

if __name__ == "__main__":
    asyncio.run(main())
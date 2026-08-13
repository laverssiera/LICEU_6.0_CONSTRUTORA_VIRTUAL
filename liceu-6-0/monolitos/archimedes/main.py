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
logger = logging.getLogger("archimedes")

async def main() -> None:
    bus = EventBus(nats_url=os.getenv("NATS_URL", "nats://nats:4222"))
    correlation_id = get_correlation_id()
    set_correlation_id(correlation_id)
    logger.info("Publicando lead.created", extra={"correlation_id": correlation_id})
    await bus.publish(
        "lead.created",
        {
            "lead_id": "lead-001",
            "origin": "archimedes",
            "status": "new",
        },
        source="archimedes",
        correlation_id=correlation_id
    )
    logger.info("Publicando deal.closed", extra={"correlation_id": correlation_id})
    await bus.publish(
        "deal.closed",
        {
            "deal_id": "deal-001",
            "lead_id": "lead-001",
            "property_id": "prop-001",
        },
        source="archimedes",
        correlation_id=correlation_id
    )
    await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
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
logger = logging.getLogger("juridicotech")

async def handler(event: dict) -> None:
    bus = handler.bus
    event_type = event.get("type")
    payload = event.get("payload", {})
    correlation_id = event.get("correlation_id") or get_correlation_id()
    set_correlation_id(correlation_id)
    logger.info(f"Evento recebido: {event_type}", extra={"correlation_id": correlation_id})

    if event_type == "deal.closed":
        proposal_payload = {
            **payload,
            "proposal_id": payload.get("deal_id", "proposal") + "-proposal",
            "proposal_status": "sent",
        }
        await bus.publish("proposal.sent", proposal_payload, source="juridicotech", correlation_id=correlation_id)
        logger.info("Proposta enviada", extra={"correlation_id": correlation_id})

    if event_type == "proposal.sent":
        contract_payload = {
            **payload,
            "contract_id": payload.get("proposal_id", "contract") + "-contract",
            "contract_status": "created",
        }
        await bus.publish("contract.created", contract_payload, source="juridicotech", correlation_id=correlation_id)
        logger.info("Contrato criado", extra={"correlation_id": correlation_id})

    if event_type == "contract.created":
        signed_payload = {
            **payload,
            "contract_status": "signed",
            "signature_provider": "juridicotech-digital-sign",
        }
        await bus.publish("contract.signed", signed_payload, source="juridicotech", correlation_id=correlation_id)
        logger.info("Contrato assinado", extra={"correlation_id": correlation_id})

    if event_type == "contract.signed":
        await bus.publish("commission.protected", payload, source="juridicotech", correlation_id=correlation_id)
        logger.info("Comissão protegida", extra={"correlation_id": correlation_id})

async def main() -> None:
    bus = EventBus(nats_url=os.getenv("NATS_URL", "nats://nats:4222"))
    handler.bus = bus
    await bus.run_forever(handler)

if __name__ == "__main__":
    asyncio.run(main())

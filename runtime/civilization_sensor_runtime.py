from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

try:
    from kafka import KafkaProducer
except Exception:  # pragma: no cover
    KafkaProducer = None

logger = logging.getLogger(__name__)


class CivilizationSensorRuntime:
    """Ingestao de stream de sensores com publicacao em NATS/Redis e Kafka."""

    def __init__(
        self,
        event_bus_publisher: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        kafka_bootstrap_servers: Optional[str] = None,
        kafka_topic: str = "civilization.sensor.stream",
        stream_channel: str = "civilization.sensor.stream",
        max_events: int = 5000,
    ) -> None:
        self._lock = RLock()
        self._events: List[Dict[str, Any]] = []
        self._event_bus_publisher = event_bus_publisher
        self._stream_channel = stream_channel
        self._max_events = max(100, max_events)

        self._kafka_topic = kafka_topic
        self._kafka_producer = None

        bootstrap = kafka_bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
        if bootstrap and KafkaProducer is not None:
            try:
                self._kafka_producer = KafkaProducer(
                    bootstrap_servers=[item.strip() for item in bootstrap.split(",") if item.strip()],
                    value_serializer=lambda v: json.dumps(v, ensure_ascii=True).encode("utf-8"),
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Kafka producer unavailable: %s", exc)
                self._kafka_producer = None

    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "twin_id": str(payload.get("twin_id") or "civilization-global"),
            "sensor_id": str(payload.get("sensor_id") or "unknown-sensor"),
            "metric": str(payload.get("metric") or "unknown"),
            "value": payload.get("value"),
            "unit": payload.get("unit") or "",
            "source": payload.get("source") or "sensor-stream",
            "tags": payload.get("tags") or {},
        }

        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]

        delivery = {
            "event_bus": self._publish_event_bus(event),
            "kafka": self._publish_kafka(event),
        }
        return {"event": event, "delivery": delivery}

    def list_recent(self, twin_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, self._max_events))
        with self._lock:
            if twin_id:
                items = [item for item in self._events if item.get("twin_id") == twin_id]
            else:
                items = list(self._events)
        return items[-safe_limit:]

    def _publish_event_bus(self, event: Dict[str, Any]) -> bool:
        if self._event_bus_publisher is None:
            return False
        try:
            self._event_bus_publisher(self._stream_channel, event)
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("Event bus publish failed: %s", exc)
            return False

    def _publish_kafka(self, event: Dict[str, Any]) -> bool:
        if self._kafka_producer is None:
            return False
        try:
            self._kafka_producer.send(self._kafka_topic, event)
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("Kafka publish failed: %s", exc)
            return False


sensor_runtime = CivilizationSensorRuntime()

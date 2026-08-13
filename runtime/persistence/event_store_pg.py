import json
import logging
from typing import Any, Dict, List
# import psycopg2
# from psycopg2.extras import Json

logger = logging.getLogger(__name__)

class EventStore:
    """
    Event Store utilizing PostgreSQL and TimescaleDB for time-series event data.
    """
    def __init__(self, connection_string: str = "dbname=liceu user=postgres password=postgres host=localhost"):
        self.connection_string = connection_string
        # Conexão mockada para demonstração - em produção usar pool assíncrono ou síncrono
        # self.conn = psycopg2.connect(self.connection_string)

    def init_db(self):
        """
        Initializes the TimescaleDB hypertable for events.
        """
        query = """
        CREATE TABLE IF NOT EXISTS civilization_events (
            time TIMESTAMPTZ NOT NULL,
            event_id UUID NOT NULL,
            event_type VARCHAR(255) NOT NULL,
            aggregate_id VARCHAR(255) NOT NULL,
            payload JSONB NOT NULL,
            metadata JSONB,
            version INT NOT NULL,
            PRIMARY KEY (event_id, time)
        );
        -- TimescaleDB Hypertable conversion (requires TimescaleDB extension)
        -- SELECT create_hypertable('civilization_events', 'time', if_not_exists => TRUE);
        """
        logger.info("Initializing TimescaleDB / PostgreSQL Event Store")
        # with self.conn.cursor() as cur:
        #     cur.execute(query)
        # self.conn.commit()

    def append_event(self, event_id: str, event_type: str, aggregate_id: str, payload: Dict[str, Any], metadata: Dict[str, Any], version: int):
        """
        Appends an event to the Event Store.
        """
        query = """
        INSERT INTO civilization_events (time, event_id, event_type, aggregate_id, payload, metadata, version)
        VALUES (NOW(), %s, %s, %s, %s, %s, %s)
        """
        logger.info(f"Appending event {event_type} for aggregate {aggregate_id}")
        # with self.conn.cursor() as cur:
        #     cur.execute(query, (event_id, event_type, aggregate_id, Json(payload), Json(metadata), version))
        # self.conn.commit()

    def get_events(self, aggregate_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all events for a given aggregate_id.
        """
        query = """
        SELECT time, event_id, event_type, aggregate_id, payload, metadata, version
        FROM civilization_events
        WHERE aggregate_id = %s
        ORDER BY time ASC
        """
        logger.info(f"Retrieving events for aggregate {aggregate_id}")
        # with self.conn.cursor() as cur:
        #     cur.execute(query, (aggregate_id,))
        #     rows = cur.fetchall()
        #     return [{"time": r[0], "event_id": r[1], "event_type": r[2], "aggregate_id": r[3], "payload": r[4], "metadata": r[5], "version": r[6]} for r in rows]
        return []

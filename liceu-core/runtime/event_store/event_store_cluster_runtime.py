import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class EventStoreClusterRuntime:
    """
    Event Store Cluster Runtime
    Single source of temporal truth for the entire ecosystem.
    Agnostic to business logic (CubeSat, Mars, BIM, etc).
    Handles events with aggregate_id, event_type, payload, correlation_id, causation_id, trace_id, etc.
    """
    def __init__(self, db_pool=None):
        """
        :param db_pool: Connection pool (e.g., asyncpg pool or SQLAlchemy engine)
                        ready to connect to PostgreSQL / TimescaleDB.
        """
        self.db_pool = db_pool

    async def append(
        self,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        """
        Appends a new event to the Event Store.
        
        Recommended DB Schema (TimescaleDB / PostgreSQL):
        CREATE TABLE event_store (
            event_id UUID PRIMARY KEY,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL,
            correlation_id TEXT,
            causation_id TEXT,
            trace_id TEXT,
            created_at TIMESTAMPTZ NOT NULL
        );
        """
        event_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        
        if self.db_pool:
            # Example using asyncpg syntax
            query = """
                INSERT INTO event_store (
                    event_id, aggregate_id, event_type, payload, 
                    correlation_id, causation_id, trace_id, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            await self.db_pool.execute(
                query, 
                event_id, 
                aggregate_id, 
                event_type, 
                json.dumps(payload),
                correlation_id, 
                causation_id, 
                trace_id, 
                created_at
            )
        
        return event_id

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all events for a given aggregate_id, ordered by creation time.
        """
        if self.db_pool:
            query = """
                SELECT * FROM event_store 
                WHERE aggregate_id = $1 
                ORDER BY created_at ASC
            """
            records = await self.db_pool.fetch(query, aggregate_id)
            return [dict(r) for r in records]
        
        return []

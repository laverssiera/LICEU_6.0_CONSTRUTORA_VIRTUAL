import asyncpg
import hashlib
import json

class TemporalEventStore:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user="postgres",
            password="liceu123",
            database="postgres",
            host="localhost"
        )

    async def append_event(self, stream, event):
        payload = json.dumps(event)
        signature = hashlib.sha256(
            payload.encode()
        ).hexdigest()

        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO runtime_events(
                    stream,
                    payload,
                    signature,
                    created_at
                )
                VALUES($1,$2,$3,NOW())
                ''',
                stream,
                payload,
                signature
            )

        return {
            "persisted": True,
            "signature": signature
        }
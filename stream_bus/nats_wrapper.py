import asyncio
from nats.aio.client import Client as NATS

class EventBus:
    def __init__(self):
        self.nc = NATS()

    async def connect(self):
        await self.nc.connect("nats://localhost:4222")

    async def publish(self, topic: str, payload: dict):
        await self.nc.publish(topic, str(payload).encode())

    async def subscribe(self, topic, handler):
        """
        Se topic == '>', faz subscribe global (wildcard) e encaminha todos eventos para handler.
        """
        async def wrapper(msg):
            await handler(msg.data.decode())
        await self.nc.subscribe(topic, cb=wrapper)

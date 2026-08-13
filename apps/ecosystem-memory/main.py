from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="Ecosystem Memory")

MEMORY = []

class MemoryEvent(BaseModel):
    monolith: str
    category: str
    event: str
    payload: dict

@app.post("/memory/store")
async def store_memory(ev: MemoryEvent):
    MEMORY.append({
        "timestamp": time.time(),
        **ev.dict()
    })
    return {"status": "stored"}

@app.get("/memory/query")
async def query_memory():
    return MEMORY

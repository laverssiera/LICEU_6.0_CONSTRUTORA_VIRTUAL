from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import uuid
import time

app = FastAPI(title="Federation Authority")

REGISTRY = {}

class MonolithRegistration(BaseModel):
    monolith_name: str
    domain: str
    version: str
    endpoint: str
    capabilities: list[str]

@app.post("/federation/register")
async def register_monolith(payload: MonolithRegistration):
    monolith_id = str(uuid.uuid4())
    REGISTRY[monolith_id] = {
        "id": monolith_id,
        "registered_at": time.time(),
        **payload.dict()
    }
    return {
        "status": "registered",
        "monolith_id": monolith_id
    }

@app.get("/federation/registry")
async def registry():
    return REGISTRY

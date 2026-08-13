from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Causal Runtime")

CAUSAL_EVENTS = []

class CausalEvent(BaseModel):
    cause: str
    effect: str
    confidence: float
    metadata: dict = {}

@app.post("/causal/link")
async def link_causality(ev: CausalEvent):
    CAUSAL_EVENTS.append(ev.dict())
    return {
        "status": "causality_registered"
    }

@app.get("/causal/map")
async def causal_map():
    return CAUSAL_EVENTS

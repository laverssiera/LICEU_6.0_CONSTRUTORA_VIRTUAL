from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="Unified Observability")

LOGS = []

class RuntimeLog(BaseModel):
    monolith: str
    level: str
    message: str
    metadata: dict = {}

@app.post("/observability/log")
async def ingest_log(log: RuntimeLog):
    LOGS.append({
        "timestamp": time.time(),
        **log.dict()
    })
    return {"status": "ingested"}

@app.get("/observability/logs")
async def get_logs():
    return LOGS

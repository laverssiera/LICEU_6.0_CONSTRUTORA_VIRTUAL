from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Knowledge Graph")

GRAPH = []

class Relation(BaseModel):
    source: str
    relation: str
    target: str
    metadata: dict = {}

@app.post("/graph/relation")
async def create_relation(rel: Relation):
    GRAPH.append(rel.dict())
    return {"status": "linked"}

@app.get("/graph")
async def get_graph():
    return GRAPH

from fastapi import FastAPI

app = FastAPI(title="Collective Mind")

THOUGHTS = []

@app.post("/collective/think")
async def think(payload: dict):
    THOUGHTS.append(payload)
    return {
        "status": "collective_thought_registered"
    }

@app.get("/collective/thoughts")
async def thoughts():
    return THOUGHTS

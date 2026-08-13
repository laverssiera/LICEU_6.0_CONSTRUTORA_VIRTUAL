from fastapi import FastAPI

app = FastAPI(title="Interplanetary Gateway")

@app.get("/interplanetary/status")
async def status():
    return {
        "earth": "online",
        "mars": "simulated",
        "moon": "simulated",
        "orbital_market": "active"
    }

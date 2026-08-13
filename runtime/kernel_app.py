import os
import sys

# Ensure the root path is correct so `runtime.*` imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import uvicorn

# Routers
from runtime.federation.federation_event_registry import router as event_registry_router
from runtime.contracts.universal_contract_validator import router as contract_validator_router
from runtime.events.event_replay_runtime import router as event_replay_router
from runtime.federation.federation_dependency_graph import router as dependency_graph_router
from runtime.federation.federation_runtime import router as federation_runtime_router
from runtime.civilization.civilization_state_runtime import router as state_runtime_router
from runtime.planetary.planet_runtime_endpoint import router as planet_runtime_router
from runtime.planetary.earth_runtime import earth_router

app = FastAPI(title="Civilization Kernel - LICEU 6.0", version="6.0.0")

app.include_router(event_registry_router)
app.include_router(contract_validator_router)
app.include_router(event_replay_router)
app.include_router(dependency_graph_router)
app.include_router(federation_runtime_router)
app.include_router(state_runtime_router)
app.include_router(planet_runtime_router)
app.include_router(earth_router)

@app.get("/")
def root():
    return RedirectResponse("/docs")

if __name__ == "__main__":
    uvicorn.run("runtime.kernel_app:app", host="0.0.0.0", port=8000, reload=True)

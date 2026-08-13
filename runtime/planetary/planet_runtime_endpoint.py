from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from runtime.planetary.earth_runtime import earth_runtime
from runtime.planetary.planet_runtime import PlanetRuntime

router = APIRouter()


class PlanetRuntimeRunRequest(BaseModel):
    cycles: int = Field(default=1, ge=1)
    cycle_interval_seconds: int = Field(default=60, ge=0)


class EarthCaseRequest(BaseModel):
    mission_name: str = Field(default="Earth Mission")
    region: str = Field(default="global")


@router.post("/planetary/runtime/run")
def run_planetary_runtime(payload: PlanetRuntimeRunRequest):
    runtime = PlanetRuntime(
        cycle_interval_seconds=payload.cycle_interval_seconds,
        max_cycles=payload.cycles,
    )
    return runtime.run()


@router.post("/planetary/earth/case")
def create_earth_case(payload: EarthCaseRequest):
    try:
        return earth_runtime.create_earth_case(
            mission_name=payload.mission_name,
            region=payload.region,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/planetary/earth/state")
def get_earth_state():
    try:
        return earth_runtime.get_earth_state()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/planetary/earth/history")
def get_earth_history():
    try:
        return earth_runtime.get_earth_history()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from runtime.contracts.registry import registry

class FederationEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_system: str = Field(..., description="System that generated the event")

# ConstructionProjectEvent
class ConstructionProjectEvent(FederationEvent):
    project_id: str
    phase: str
    budget_status: str
    milestones_completed: int

# SatelliteMissionEvent
class SatelliteMissionEvent(FederationEvent):
    mission_id: str
    orbit_status: str
    telemetry_data: Dict[str, Any]

# CityPlanningEvent
class CityPlanningEvent(FederationEvent):
    zone_id: str
    zoning_changes: str
    approval_status: str

# MobilityNetworkEvent
class MobilityNetworkEvent(FederationEvent):
    route_id: str
    congestion_level: float
    active_vehicles: int

# DigitalTwinEvent
class DigitalTwinEvent(FederationEvent):
    twin_id: str
    synchronization_latency_ms: float
    state_diff: Dict[str, Any]

# Register models in the central registry
registry.register("federation", "1", "ConstructionProjectEvent", ConstructionProjectEvent)
registry.register("federation", "1", "SatelliteMissionEvent", SatelliteMissionEvent)
registry.register("federation", "1", "CityPlanningEvent", CityPlanningEvent)
registry.register("federation", "1", "MobilityNetworkEvent", MobilityNetworkEvent)
registry.register("federation", "1", "DigitalTwinEvent", DigitalTwinEvent)

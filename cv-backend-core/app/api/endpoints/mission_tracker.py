from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

# We simulate the modules we created
from command_center.mission_lifecycle_dashboard import MissionLifecycleDashboard

router = APIRouter()

@router.get("/status")
def get_mission_lifecycle_dashboard() -> List[Dict[str, Any]]:
    # Mock Data logic as built previously, but served over JSON/HTTP
    m1_id = str(uuid.uuid4())
    m2_id = str(uuid.uuid4())
    
    mock_registry = [
        {"mission_id": m1_id, "charter": "Expansão de Causal Runtime", "stakeholders": ["Admin", "AI_Core"], "contracts": ["C-1", "C-2"]},
        {"mission_id": m2_id, "charter": "Manutenção do Knowledge Graph", "stakeholders": ["Data_Ops"], "contracts": ["C-3"]},
        {"mission_id": str(uuid.uuid4()), "charter": "Integração Federation-UI", "stakeholders": ["Frontend_Team", "Backend_Team"], "contracts": ["C-4"]}
    ]
    
    mock_cost = [
        {"mission_id": m1_id, "budget": 500000, "spent": 120000, "status": "UNDER_BUDGET"},
        {"mission_id": m2_id, "budget": 100000, "spent": 95000, "status": "WARNING_NEAR_LIMIT"},
        {"mission_id": mock_registry[2]["mission_id"], "budget": 300000, "spent": 310000, "status": "OVER_BUDGET"}
    ]
    
    overrides = {m2_id: "BLOCKED"}
    
    dashboard = MissionLifecycleDashboard()
    result = dashboard.aggregate_mission_data(mock_registry, mock_cost, overrides)
    
    # Sort just for consistent UI
    result.sort(key=lambda x: x["lifecycle_state"])
    return result

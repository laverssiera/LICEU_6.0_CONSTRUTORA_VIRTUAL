import json
from datetime import datetime
import uuid

class MissionLifecycleDashboard:
    def __init__(self):
        self.dashboard_views = []

    def aggregate_mission_data(self, registry_data: list, cost_data: list, status_overrides: dict = None):
        """
        Merge registry info and cost tracking info into a unified view.
        status_overrides simulates external signals (like a blocking issue).
        """
        status_overrides = status_overrides or {}
        dashboard = []

        for m_reg in registry_data:
            m_id = m_reg["mission_id"]
            m_cost = next((c for c in cost_data if c["mission_id"] == m_id), None)
            
            # Determine overall health/lifecycle state
            state = "RUNNING"
            health = "GREEN"

            if status_overrides.get(m_id) == "BLOCKED":
                state = "BLOCKED"
                health = "RED"
            elif m_cost and m_cost["status"] == "OVER_BUDGET":
                health = "YELLOW"
            elif m_cost and m_cost["status"] == "WARNING_NEAR_LIMIT":
                health = "YELLOW"
                
            dashboard.append({
                "mission_id": m_id,
                "name": m_reg.get("charter", "Unknown Charter"),
                "lifecycle_state": state,
                "health": health,
                "stakeholders": m_reg.get("stakeholders", []),
                "contracts_active": len(m_reg.get("contracts", [])),
                "budget_spent_pct": round((m_cost["spent"] / m_cost["budget"] * 100), 2) if m_cost and m_cost["budget"] > 0 else 0,
                "last_updated": datetime.utcnow().isoformat()
            })

        self.dashboard_views = dashboard
        return dashboard

    def render_dashboard(self):
        print("="*60)
        print("🚀 MISSION LIFECYCLE DASHBOARD 🚀")
        print("="*60)
        for view in self.dashboard_views:
            print(f"Mission: {view['name']} [{view['mission_id'][:8]}...]")
            print(f"State: {view['lifecycle_state']} | Health: {view['health']}")
            print(f"Stakeholders: {', '.join(view['stakeholders'])}")
            print(f"Contracts: {view['contracts_active']} | Budget Spent: {view['budget_spent_pct']}%")
            print("-" * 60)

if __name__ == "__main__":
    print("📊 Integrando Mission Lifecycle Dashboard...")
    
    # Mock Data to simulate pulling from Registry and Cost Tracker
    m1_id = str(uuid.uuid4())
    m2_id = str(uuid.uuid4())
    
    mock_registry = [
        {"mission_id": m1_id, "charter": "Expansão de Causal Runtime", "stakeholders": ["Admin", "AI_Core"], "contracts": ["C-1", "C-2"]},
        {"mission_id": m2_id, "charter": "Manutenção do Knowledge Graph", "stakeholders": ["Data_Ops"], "contracts": ["C-3"]}
    ]
    
    mock_cost = [
        {"mission_id": m1_id, "budget": 500000, "spent": 120000, "status": "UNDER_BUDGET"},
        {"mission_id": m2_id, "budget": 100000, "spent": 95000, "status": "WARNING_NEAR_LIMIT"}
    ]
    
    overrides = {m2_id: "BLOCKED"}
    
    dashboard = MissionLifecycleDashboard()
    dashboard.aggregate_mission_data(mock_registry, mock_cost, overrides)
    dashboard.render_dashboard()

import json
from datetime import datetime
import uuid

class MissionCostTracker:
    def __init__(self):
        # Maps mission_id -> cost data
        self.cost_records = {}

    def init_mission_budget(self, mission_id: str, budget: float, currency: str = "CREDITS"):
        self.cost_records[mission_id] = {
            "mission_id": mission_id,
            "budget": budget,
            "currency": currency,
            "spent": 0.0,
            "transactions": [],
            "status": "UNDER_BUDGET"
        }
        return self.cost_records[mission_id]

    def record_cost(self, mission_id: str, amount: float, description: str, monolith_source: str):
        if mission_id not in self.cost_records:
            raise ValueError(f"Mission {mission_id} not initialized in Cost Tracker.")
        
        record = self.cost_records[mission_id]
        record["spent"] += amount
        record["transactions"].append({
            "tx_id": str(uuid.uuid4()),
            "amount": amount,
            "description": description,
            "source": monolith_source,
            "timestamp": datetime.utcnow().isoformat()
        })

        if record["spent"] > record["budget"]:
            record["status"] = "OVER_BUDGET"
        elif record["spent"] > record["budget"] * 0.9:
            record["status"] = "WARNING_NEAR_LIMIT"

        return record

    def get_mission_cost_summary(self, mission_id: str):
        return self.cost_records.get(mission_id)

    def generate_global_cost_report(self):
        return {
            "total_budget_allocated": sum(r["budget"] for r in self.cost_records.values()),
            "total_spent": sum(r["spent"] for r in self.cost_records.values()),
            "missions": self.cost_records
        }

if __name__ == "__main__":
    print("💰 Inicializando Mission Cost Tracking...")
    tracker = MissionCostTracker()
    m_id = str(uuid.uuid4())
    
    tracker.init_mission_budget(m_id, 1000000.0)
    tracker.record_cost(m_id, 150000.0, "Alocação de GPU na Federação", "federation-authority")
    tracker.record_cost(m_id, 50000.0, "Consulta Otimizada no Grafo", "knowledge-graph")
    
    report = tracker.get_mission_cost_summary(m_id)
    print(f"✅ Mission {m_id} Cost Summary:\n{json.dumps(report, indent=2)}")

import uuid
import datetime
import json

class MissionRegistryRuntime:
    def __init__(self):
        self.missions = {}

    def create_mission(self, name, scope, stakeholders):
        mission_id = str(uuid.uuid4())
        mission = {
            "mission_id": mission_id,
            "charter": f"Charter for {name}",
            "scope": scope,
            "stakeholders": stakeholders,
            "contracts": [],
            "audit_trail": [
                {"event": "MISSION_INITIATED", "timestamp": datetime.datetime.utcnow().isoformat()}
            ]
        }
        self.missions[mission_id] = mission
        return mission_id

    def add_contract(self, mission_id, contract_id):
        if mission_id in self.missions:
            self.missions[mission_id]["contracts"].append(contract_id)
            self.missions[mission_id]["audit_trail"].append({
                "event": "CONTRACT_ADDED",
                "contract_id": contract_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })

    def get_mission(self, mission_id):
        return self.missions.get(mission_id)

if __name__ == "__main__":
    print("🚀 Inicializando Mission Registry Runtime...")
    registry = MissionRegistryRuntime()
    m_id = registry.create_mission(
        "Missão Interplanetária Federada",
        "Estabelecimento de infraestrutura unificada do ecossistema",
        ["LICEU_CORE", "Federação", "Stakeholders"]
    )
    print(f"✅ Mission Created:\n{json.dumps(registry.get_mission(m_id), indent=2)}\n")

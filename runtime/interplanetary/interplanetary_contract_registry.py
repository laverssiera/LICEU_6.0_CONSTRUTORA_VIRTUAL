import json
import uuid

class InterplanetaryContractRegistry:
    VALID_TYPES = ["MSA", "SoW", "TRD", "MAP", "RMP", "DMP", "IPA"]

    def __init__(self):
        self.contracts = {}

    def register_contract(self, c_type, parties, details):
        if c_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid contract type. Must be one of: {self.VALID_TYPES}")
        
        c_id = f"CONTRACT-{c_type}-{str(uuid.uuid4())[:8]}"
        contract = {
            "contract_id": c_id,
            "type": c_type,
            "parties": parties,
            "details": details,
            "status": "ACTIVE"
        }
        self.contracts[c_id] = contract
        return contract

if __name__ == "__main__":
    print("📜 Inicializando Interplanetary Contract Registry...")
    registry = InterplanetaryContractRegistry()
    types_to_create = ["MSA", "SoW", "TRD", "MAP", "RMP", "DMP", "IPA"]
    
    for t in types_to_create:
        c = registry.register_contract(
            t, 
            ["LICEU_CORE", "Missão Interplanetária"], 
            {"description": f"Standard {t} agreement for Interplanetary Mission"}
        )
        print(f"✅ Registered Contract: {c['contract_id']} (Type: {c['type']})")
    
    print("\n")
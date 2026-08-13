import uuid
import sys
import os

# Adiciona o diretorio base no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runtime.persistence.universal_store import universal_store
import datetime
import json

def launch_cubesat():
    mission_id = f"mission-cubesat-6u-{uuid.uuid4().hex[:8]}"
    print(f"🚀 Iniciando Missão: {mission_id}")
    
    # 1. Mission Ledger
    mission_data = {
        "mission_name": "CubeSat 6U Science",
        "description": "Observação orbital e prospecção de materiais espaciais.",
        "type": "CUBESAT_6U",
        "objectives": ["Observação orbital", "Materiais espaciais"],
        "gate": "Gate 4 - Liceu Core",
        "status": "INITIATED"
    }
    universal_store.save_mission(mission_id, mission_data)
    
    # 2. Decision Trail
    decision_id = f"trail_{mission_id}_init"
    universal_store.save_decision_trail(decision_id, {
        "action": "MISSION_APPROVED_AND_INITIATED",
        "details": "Aprovada missão estratégica de CubeSat 6U baseada nas diretrizes do Liceu Core",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    
    # 3. Event Store
    evt_id = f"evt_{mission_id}_start"
    universal_store.save_federation_event(evt_id, "MISSION_LIFECYCLE_STARTED", {
        "mission_id": mission_id,
        "gate": "Gate 4 - Liceu Core",
        "payload": mission_data
    })
    
    # 4. Trust Ledger (Trust Chain)
    universal_store.save_trust_chain(
        node_a="Liceu_Core_Gate_4",
        node_b=mission_id,
        relationship="GOVERNS_MISSION"
    )
    
    # 5. Semantic Memory to aid retrieval
    universal_store.index_semantic_memory(
        doc_id=mission_id,
        text="Missão CubeSat 6U. Observação orbital e materiais espaciais. Lançamento aprovado via Gate 4.",
        vector_embedding=[0.9, 0.8, 0.1]
    )

    print("✅ Missão CubeSat 6U registrada com sucesso em todos os ledgers (Mission Ledger, Trust Ledger, Event Store, Decision Trail).")
    print(json.dumps(mission_data, indent=2))

if __name__ == "__main__":
    launch_cubesat()

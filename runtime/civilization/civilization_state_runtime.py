import random
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

class CivilizationStateRuntime:
    """
    O "Pulso Vital" do ecossistema inteiro.
    Inspeciona o snapshot consolidado de toda a federação no momento atual.
    """
    def __init__(self):
        pass

    def get_global_pulse(self) -> Dict[str, Any]:
        """
        Retorna as principais métricas que balizam LICEU = Civilization Kernel.
        Na vida real essas metricas vêm através de agregações rápidas (Redis)
        projetadas no topo do Event Store.
        """
        return {
            "civilization_status": "EXPANDING",
            "metrics": {
                "missions_active": random.randint(15, 45),
                "contracts_active": random.randint(1200, 2000),
                "twins_active": random.randint(300, 500),
                "scientific_experiments": random.randint(5, 20),
                "construction_projects": random.randint(10, 30),
                "financial_exposure": f"${random.uniform(1.5, 5.0):.2f}B",
                "federation_health": "99.98%"
            },
            "critical_alerts": []
        }

state_runtime = CivilizationStateRuntime()

@router.get("/civilization/state")
def get_civilization_state():
    return state_runtime.get_global_pulse()
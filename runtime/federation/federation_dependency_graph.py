from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()

class FederationDependencyGraph:
    """
    Controla dependências entre todos os monólitos do LICEU.
    Identifica falhas em cascata se um nó cai (ex: ARCHIMEDES caindo impacta Twins, Contratos, etc)
    """
    def __init__(self):
        # Directed graph indicating what depends on what
        self.graph = {
            "ARCHIMEDES": {
                "impacts_missions": ["MARS_HABITAT_ALPHA", "LUNAR_BASE_BETA"],
                "impacts_twins": ["TWIN_SAT_01", "TWIN_MECHNODE"],
                "impacts_contracts": ["SUPPLIER_STEEL_001"],
                "impacts_suppliers": ["TECH_CONST_Corp"]
            },
            "BIM": {
                "impacts_missions": ["EARTH_MEGACITY_01"],
                "impacts_twins": ["TWIN_BUILDING_BR", "TWIN_TUNNEL_04"],
                "impacts_contracts": ["TUNNEL_INFRA_CONTRACT"],
                "impacts_suppliers": ["CONCRETE_GLOBAL"]
            },
            "OPERA": {
                "impacts_missions": ["ALL_SCHEDULED_MISSIONS"],
                "impacts_twins": [],
                "impacts_contracts": ["HR_CONTRACTS", "OPERATIONAL_SLA"],
                "impacts_suppliers": ["ALL_LOGISTICS"]
            },
            "JOHN": {
                "impacts_missions": ["DEEP_SPACE_PROBE"],
                "impacts_twins": ["ALL_AI_TWINS"],
                "impacts_contracts": ["RESEARCH_GRANT_01"],
                "impacts_suppliers": ["COMPUTE_CLOUD_PROVIDERS"]
            }
        }

    def simulate_node_failure(self, node_name: str) -> Dict[str, Any]:
        node = node_name.upper()
        if node not in self.graph:
            return {"status": "SAFE", "message": f"{node} is not in dependency graph or has no critical downstream impacts."}
            
        return {
            "status": "CRITICAL_IMPACT",
            "failed_node": node,
            "blast_radius": self.graph[node]
        }

dependency_graph = FederationDependencyGraph()

@router.get("/federation/dependency/{node}/impact")
def get_node_impact(node: str):
    return dependency_graph.simulate_node_failure(node)
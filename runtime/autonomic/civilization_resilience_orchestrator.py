from fastapi import APIRouter
import networkx as nx
import hashlib
import statistics
import random
import psutil
import time

router = APIRouter()

ORCHESTRATION_MEMORY = []

ORCHESTRATION_GRAPH = nx.DiGraph()

RUNTIME_COMPONENTS = [
    "civilization_autonomic_runtime",
    "sovereign_defense_mesh",
    "adaptive_mutation_runtime",
    "autonomous_healing_mesh"
]

ORCHESTRATION_ACTIONS = [
    "rebalance federation",
    "stabilize cognition mesh",
    "optimize resilience topology",
    "synchronize sovereign runtimes",
    "restore civilization continuity",
    "amplify adaptive orchestration",
    "reconstruct runtime lineage",
    "preserve distributed equilibrium"
]

class CivilizationResilienceOrchestrator:

    @staticmethod
    def orchestrate(payload):
        federation_pressure = float(
            payload.get(
                "federation_pressure",
                random.uniform(0.75, 1.0)
            )
        )
        resilience_target = float(
            payload.get(
                "resilience_target",
                random.uniform(0.90, 1.0)
            )
        )
        cognition_load = float(
            payload.get(
                "cognition_load",
                random.uniform(0.75, 1.0)
            )
        )

        cpu_load = psutil.cpu_percent()
        memory_load = (
            psutil.virtual_memory().percent
        )

        runtime_states = []

        for component in RUNTIME_COMPONENTS:
            component_health = round(
                statistics.mean([
                    random.uniform(0.88, 1.0),
                    federation_pressure,
                    resilience_target,
                    cognition_load
                ]),
                6
            )

            runtime_states.append({
                "component": component,
                "health": component_health
            })

        runtime_states.sort(
            key=lambda x: x["health"]
        )

        weakest_component = runtime_states[0]

        orchestration_action = random.choice(
            ORCHESTRATION_ACTIONS
        )

        civilization_resilience = statistics.mean([
            federation_pressure,
            resilience_target,
            cognition_load,
            1 - (cpu_load / 100),
            1 - (memory_load / 100)
        ])

        orchestration_state = {
            "timestamp": time.time(),
            "runtime_states": runtime_states,
            "weakest_component": weakest_component,
            "orchestration_action": orchestration_action,
            "cpu_load": cpu_load,
            "memory_load": memory_load,
            "federation_pressure": federation_pressure,
            "resilience_target": resilience_target,
            "cognition_load": cognition_load,
            "civilization_resilience": round(
                civilization_resilience,
                6
            ),
            "runtime_identity": "civilization_resilience_orchestrator"
        }

        orchestration_signature = hashlib.sha256(
            str(orchestration_state).encode()
        ).hexdigest()

        orchestration_state["orchestration_signature"] = orchestration_signature

        ORCHESTRATION_MEMORY.append(
            orchestration_state
        )

        if len(ORCHESTRATION_MEMORY) > 1:
            previous_signature = (
                ORCHESTRATION_MEMORY[-2]["orchestration_signature"]
            )
            ORCHESTRATION_GRAPH.add_edge(
                previous_signature,
                orchestration_signature
            )

        equilibrium_index = statistics.mean([
            x["civilization_resilience"]
            for x in ORCHESTRATION_MEMORY
        ])

        civilization_stability = round(
            1 - abs(
                equilibrium_index - 0.99
            ),
            6
        )

        return {
            "orchestration_state": orchestration_state,
            "equilibrium_index": round(
                equilibrium_index,
                6
            ),
            "civilization_stability": civilization_stability,
            "memory_size": len(
                ORCHESTRATION_MEMORY
            ),
            "graph_nodes": ORCHESTRATION_GRAPH.number_of_nodes(),
            "graph_edges": ORCHESTRATION_GRAPH.number_of_edges(),
            "runtime_state": "civilization_orchestration_active"
        }

    @staticmethod
    def orchestration_status():
        if not ORCHESTRATION_MEMORY:
            return {
                "status": "orchestrator_not_initialized"
            }

        latest = ORCHESTRATION_MEMORY[-1]

        equilibrium_index = statistics.mean([
            x["civilization_resilience"]
            for x in ORCHESTRATION_MEMORY
        ])

        civilization_stability = round(
            1 - abs(
                equilibrium_index - 0.99
            ),
            6
        )

        return {
            "latest_orchestration": latest,
            "equilibrium_index": round(
                equilibrium_index,
                6
            ),
            "civilization_stability": civilization_stability,
            "runtime_state": "civilization_resilience_orchestrating"
        }

    @staticmethod
    def orchestration_history(limit=20):
        limit = max(1, min(limit, 1000))
        return ORCHESTRATION_MEMORY[-limit:]


@router.post("/civilization/orchestration/execute")
async def execute_orchestration(payload: dict):
    result = CivilizationResilienceOrchestrator.orchestrate(payload)
    return {"result": result}

@router.get("/civilization/orchestration/status")
async def orchestration_status():
    result = CivilizationResilienceOrchestrator.orchestration_status()
    return {"result": result}

@router.get("/civilization/orchestration/history")
async def orchestration_history(limit: int = 20):
    result = CivilizationResilienceOrchestrator.orchestration_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "civilization_resilience_orchestrator"
    }
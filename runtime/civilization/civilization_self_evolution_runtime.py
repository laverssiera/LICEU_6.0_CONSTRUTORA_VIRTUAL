from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np
import hashlib
import statistics
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

EVOLUTION_MEMORY = []

EVOLUTION_GRAPH = nx.DiGraph()

EVOLUTION_CAPABILITIES = [
    "distributed cognition",
    "federated memory",
    "metacognitive reasoning",
    "collective intention",
    "temporal consciousness",
    "autonomous governance",
    "civilization observability",
    "sovereign orchestration",
    "economic intelligence",
    "educational cognition"
]

class CivilizationSelfEvolutionRuntime:

    @staticmethod
    def evolve(payload):
        objective = payload.get(
            "objective",
            "maximize collective intelligence"
        )
        current_state = payload.get(
            "current_state",
            "civilization operational"
        )

        objective_embedding = (
            model.encode([objective])[0]
        )
        state_embedding = (
            model.encode([current_state])[0]
        )
        capability_embeddings = model.encode(
            EVOLUTION_CAPABILITIES
        )

        capability_scores = []

        for capability, embedding in zip(
            EVOLUTION_CAPABILITIES,
            capability_embeddings
        ):
            objective_similarity = np.dot(
                objective_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    objective_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            state_similarity = np.dot(
                state_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    state_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            evolution_score = (
                objective_similarity +
                state_similarity
            ) / 2

            capability_scores.append({
                "capability": capability,
                "score": round(
                    float(evolution_score),
                    6
                )
            })

        capability_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        selected_capability = (
            capability_scores[0]
        )

        evolution_index = statistics.mean([
            x["score"]
            for x in capability_scores[:3]
        ])

        evolution_state = {
            "timestamp": time.time(),
            "objective": objective,
            "current_state": current_state,
            "selected_capability": selected_capability,
            "top_capabilities": capability_scores[:5],
            "evolution_index": round(
                evolution_index,
                6
            ),
            "runtime_identity": "civilization_self_evolution_runtime"
        }

        evolution_signature = hashlib.sha256(
            str(evolution_state).encode()
        ).hexdigest()

        evolution_state["evolution_signature"] = evolution_signature

        EVOLUTION_MEMORY.append(
            evolution_state
        )

        if len(EVOLUTION_MEMORY) > 1:
            previous_signature = (
                EVOLUTION_MEMORY[-2]["evolution_signature"]
            )
            EVOLUTION_GRAPH.add_edge(
                previous_signature,
                evolution_signature
            )

        civilization_evolution = statistics.mean([
            x["evolution_index"]
            for x in EVOLUTION_MEMORY
        ])

        adaptive_stability = round(
            1 - abs(
                civilization_evolution - 0.93
            ),
            6
        )

        return {
            "evolution_state": evolution_state,
            "civilization_evolution": round(
                civilization_evolution,
                6
            ),
            "adaptive_stability": adaptive_stability,
            "memory_size": len(
                EVOLUTION_MEMORY
            ),
            "graph_nodes": EVOLUTION_GRAPH.number_of_nodes(),
            "graph_edges": EVOLUTION_GRAPH.number_of_edges(),
            "runtime_state": "self_evolving_civilization"
        }

    @staticmethod
    def evolution_state():
        if not EVOLUTION_MEMORY:
            return {
                "status": "evolution_not_initialized"
            }

        latest = EVOLUTION_MEMORY[-1]

        civilization_evolution = statistics.mean([
            x["evolution_index"]
            for x in EVOLUTION_MEMORY
        ])

        adaptive_stability = round(
            1 - abs(
                civilization_evolution - 0.93
            ),
            6
        )

        return {
            "latest_evolution": latest,
            "civilization_evolution": round(
                civilization_evolution,
                6
            ),
            "adaptive_stability": adaptive_stability,
            "runtime_state": "civilization_self_evolving"
        }

    @staticmethod
    def evolution_history(limit=20):
        limit = max(1, min(limit, 1000))
        return EVOLUTION_MEMORY[-limit:]


@router.post("/civilization/evolution/evolve")
async def evolve_civilization(payload: dict):
    result = CivilizationSelfEvolutionRuntime.evolve(payload)
    return {"result": result}

@router.get("/civilization/evolution/state")
async def civilization_evolution_state():
    result = CivilizationSelfEvolutionRuntime.evolution_state()
    return {"result": result}

@router.get("/civilization/evolution/history")
async def civilization_evolution_history(limit: int = 20):
    result = CivilizationSelfEvolutionRuntime.evolution_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "civilization_self_evolution_runtime"
    }
from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np
import hashlib
import statistics
import random
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

MUTATION_MEMORY = []

MUTATION_GRAPH = nx.DiGraph()

MUTATION_CAPABILITIES = [
    "expand cognition mesh",
    "optimize federation topology",
    "increase semantic resilience",
    "stabilize governance graph",
    "accelerate temporal reasoning",
    "improve adaptive memory",
    "reconstruct distributed lineage",
    "optimize civilization orchestration",
    "strengthen sovereign identity",
    "amplify metacognitive continuity"
]

MUTATION_ACTIONS = [
    "federation rebalance",
    "semantic restructuring",
    "cognition amplification",
    "runtime topology mutation",
    "adaptive orchestration",
    "governance reinforcement",
    "memory continuity optimization",
    "distributed cognition mutation"
]

class AdaptiveMutationRuntime:

    @staticmethod
    def mutate(payload):
        civilization_pressure = float(
            payload.get(
                "civilization_pressure",
                random.uniform(0.7, 1.0)
            )
        )
        resilience_score = float(
            payload.get(
                "resilience_score",
                random.uniform(0.7, 1.0)
            )
        )
        evolution_goal = payload.get(
            "evolution_goal",
            "maximize adaptive resilience"
        )

        goal_embedding = (
            model.encode([evolution_goal])[0]
        )
        capability_embeddings = model.encode(
            MUTATION_CAPABILITIES
        )

        mutation_scores = []

        for capability, embedding in zip(
            MUTATION_CAPABILITIES,
            capability_embeddings
        ):
            similarity = np.dot(
                goal_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    goal_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            mutation_scores.append({
                "capability": capability,
                "score": round(
                    float(similarity),
                    6
                )
            })

        mutation_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        selected_mutation = (
            mutation_scores[0]
        )

        mutation_action = random.choice(
            MUTATION_ACTIONS
        )

        adaptive_mutation_score = statistics.mean([
            civilization_pressure,
            resilience_score,
            selected_mutation["score"]
        ])

        mutation_state = {
            "timestamp": time.time(),
            "evolution_goal": evolution_goal,
            "selected_mutation": selected_mutation,
            "mutation_action": mutation_action,
            "civilization_pressure": civilization_pressure,
            "resilience_score": resilience_score,
            "adaptive_mutation_score": round(
                adaptive_mutation_score,
                6
            ),
            "runtime_identity": "adaptive_mutation_runtime"
        }

        mutation_signature = hashlib.sha256(
            str(mutation_state).encode()
        ).hexdigest()

        mutation_state["mutation_signature"] = mutation_signature

        MUTATION_MEMORY.append(
            mutation_state
        )

        if len(MUTATION_MEMORY) > 1:
            previous_signature = (
                MUTATION_MEMORY[-2]["mutation_signature"]
            )
            MUTATION_GRAPH.add_edge(
                previous_signature,
                mutation_signature
            )

        civilization_mutation_index = statistics.mean([
            x["adaptive_mutation_score"]
            for x in MUTATION_MEMORY
        ])

        adaptive_evolution = round(
            1 - abs(
                civilization_mutation_index - 0.97
            ),
            6
        )

        return {
            "mutation_state": mutation_state,
            "civilization_mutation_index": round(
                civilization_mutation_index,
                6
            ),
            "adaptive_evolution": adaptive_evolution,
            "memory_size": len(
                MUTATION_MEMORY
            ),
            "graph_nodes": MUTATION_GRAPH.number_of_nodes(),
            "graph_edges": MUTATION_GRAPH.number_of_edges(),
            "runtime_state": "adaptive_mutation_operational"
        }

    @staticmethod
    def mutation_status():
        if not MUTATION_MEMORY:
            return {
                "status": "mutation_runtime_not_initialized"
            }

        latest = MUTATION_MEMORY[-1]

        civilization_mutation_index = statistics.mean([
            x["adaptive_mutation_score"]
            for x in MUTATION_MEMORY
        ])

        adaptive_evolution = round(
            1 - abs(
                civilization_mutation_index - 0.97
            ),
            6
        )

        return {
            "latest_mutation": latest,
            "civilization_mutation_index": round(
                civilization_mutation_index,
                6
            ),
            "adaptive_evolution": adaptive_evolution,
            "runtime_state": "civilization_mutating"
        }

    @staticmethod
    def mutation_history(limit=20):
        limit = max(1, min(limit, 1000))
        return MUTATION_MEMORY[-limit:]


@router.post("/civilization/mutation/execute")
async def execute_mutation(payload: dict):
    result = AdaptiveMutationRuntime.mutate(payload)
    return {"result": result}

@router.get("/civilization/mutation/status")
async def mutation_status():
    result = AdaptiveMutationRuntime.mutation_status()
    return {"result": result}

@router.get("/civilization/mutation/history")
async def mutation_history(limit: int = 20):
    result = AdaptiveMutationRuntime.mutation_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "adaptive_mutation_runtime"
    }
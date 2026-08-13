from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import hashlib
import statistics
import numpy as np
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

INTENTION_MEMORY = []

INTENTION_GRAPH = nx.DiGraph()

CIVILIZATION_OBJECTIVES = [
    "maximize civilization stability",
    "expand federated cognition",
    "preserve sovereign continuity",
    "increase collective intelligence",
    "protect distributed governance",
    "optimize educational evolution",
    "sustain economic resilience"
]

class CollectiveIntentionRuntime:

    @staticmethod
    def synthesize(payload):
        cognition = payload.get(
            "cognition",
            "federated cognition"
        )
        reflection = payload.get(
            "reflection",
            "collective introspection"
        )

        cognition_embedding = (
            model.encode([cognition])[0]
        )
        reflection_embedding = (
            model.encode([reflection])[0]
        )
        objective_embeddings = model.encode(
            CIVILIZATION_OBJECTIVES
        )

        objective_scores = []

        for objective, embedding in zip(
            CIVILIZATION_OBJECTIVES,
            objective_embeddings
        ):
            cognition_similarity = np.dot(
                cognition_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    cognition_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            reflection_similarity = np.dot(
                reflection_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    reflection_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            final_score = (
                cognition_similarity +
                reflection_similarity
            ) / 2

            objective_scores.append({
                "objective": objective,
                "score": round(
                    float(final_score),
                    6
                )
            })

        objective_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        selected_objective = (
            objective_scores[0]
        )

        intention_state = {
            "timestamp": time.time(),
            "cognition": cognition,
            "reflection": reflection,
            "selected_objective": selected_objective,
            "top_objectives": objective_scores[:3],
            "runtime_identity": "collective_intention_runtime"
        }

        intention_signature = hashlib.sha256(
            str(intention_state).encode()
        ).hexdigest()

        intention_state["intention_signature"] = intention_signature

        INTENTION_MEMORY.append(
            intention_state
        )

        if len(INTENTION_MEMORY) > 1:
            previous_signature = (
                INTENTION_MEMORY[-2]["intention_signature"]
            )
            INTENTION_GRAPH.add_edge(
                previous_signature,
                intention_signature
            )

        strategic_alignment = statistics.mean([
            x["selected_objective"]["score"]
            for x in INTENTION_MEMORY
        ])

        return {
            "intention_state": intention_state,
            "strategic_alignment": round(
                strategic_alignment,
                6
            ),
            "memory_size": len(
                INTENTION_MEMORY
            ),
            "graph_nodes": INTENTION_GRAPH.number_of_nodes(),
            "graph_edges": INTENTION_GRAPH.number_of_edges(),
            "runtime_state": "collective_intention_active"
        }

    @staticmethod
    def intention_state():
        if not INTENTION_MEMORY:
            return {
                "status": "intention_not_initialized"
            }

        latest = INTENTION_MEMORY[-1]

        strategic_alignment = statistics.mean([
            x["selected_objective"]["score"]
            for x in INTENTION_MEMORY
        ])

        return {
            "latest_intention": latest,
            "strategic_alignment": round(
                strategic_alignment,
                6
            ),
            "runtime_state": "civilization_intention_operational"
        }

    @staticmethod
    def intention_history(limit=20):
        limit = max(1, min(limit, 1000))
        return INTENTION_MEMORY[-limit:]


@router.post("/civilization/intention/synthesize")
async def synthesize_intention(payload: dict):
    result = CollectiveIntentionRuntime.synthesize(payload)
    return {"result": result}

@router.get("/civilization/intention/state")
async def intention_state():
    result = CollectiveIntentionRuntime.intention_state()
    return {"result": result}

@router.get("/civilization/intention/history")
async def intention_history(limit: int = 20):
    result = CollectiveIntentionRuntime.intention_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "collective_intention_runtime"
    }
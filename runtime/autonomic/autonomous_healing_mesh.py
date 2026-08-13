from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np
import hashlib
import statistics
import random
import psutil
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

HEALING_MEMORY = []

HEALING_GRAPH = nx.DiGraph()

DEGRADATION_PATTERNS = [
    "federation instability",
    "runtime degradation",
    "memory fragmentation",
    "semantic inconsistency",
    "causal corruption",
    "governance instability",
    "distributed latency",
    "consensus degradation",
    "cognition imbalance",
    "identity desynchronization"
]

HEALING_ACTIONS = [
    "rebuild cognition graph",
    "restore federation topology",
    "reconstruct semantic continuity",
    "stabilize governance runtime",
    "repair distributed memory",
    "restore consensus lineage",
    "heal sovereign identity",
    "reorganize cognition mesh",
    "restore causal integrity",
    "recover civilization continuity"
]

class AutonomousHealingMesh:

    @staticmethod
    def heal(payload):
        degradation_signal = payload.get(
            "degradation_signal",
            "runtime instability"
        )
        resilience_factor = float(
            payload.get(
                "resilience_factor",
                random.uniform(0.75, 1.0)
            )
        )
        cognition_integrity = float(
            payload.get(
                "cognition_integrity",
                random.uniform(0.75, 1.0)
            )
        )

        cpu_load = psutil.cpu_percent()
        memory_load = (
            psutil.virtual_memory().percent
        )

        signal_embedding = (
            model.encode([degradation_signal])[0]
        )
        degradation_embeddings = model.encode(
            DEGRADATION_PATTERNS
        )

        degradation_scores = []

        for degradation, embedding in zip(
            DEGRADATION_PATTERNS,
            degradation_embeddings
        ):
            similarity = np.dot(
                signal_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    signal_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            degradation_scores.append({
                "degradation": degradation,
                "score": round(
                    float(similarity),
                    6
                )
            })

        degradation_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        primary_degradation = (
            degradation_scores[0]
        )

        healing_action = random.choice(
            HEALING_ACTIONS
        )

        healing_score = statistics.mean([
            resilience_factor,
            cognition_integrity,
            1 - (cpu_load / 100),
            1 - (memory_load / 100)
        ])

        recovery_index = round(
            healing_score *
            cognition_integrity,
            6
        )

        healing_state = {
            "timestamp": time.time(),
            "degradation_signal": degradation_signal,
            "primary_degradation": primary_degradation,
            "healing_action": healing_action,
            "cpu_load": cpu_load,
            "memory_load": memory_load,
            "resilience_factor": resilience_factor,
            "cognition_integrity": cognition_integrity,
            "healing_score": round(
                healing_score,
                6
            ),
            "recovery_index": recovery_index,
            "runtime_identity": "autonomous_healing_mesh"
        }

        healing_signature = hashlib.sha256(
            str(healing_state).encode()
        ).hexdigest()

        healing_state["healing_signature"] = healing_signature

        HEALING_MEMORY.append(
            healing_state
        )

        if len(HEALING_MEMORY) > 1:
            previous_signature = (
                HEALING_MEMORY[-2]["healing_signature"]
            )
            HEALING_GRAPH.add_edge(
                previous_signature,
                healing_signature
            )

        civilization_recovery = statistics.mean([
            x["recovery_index"]
            for x in HEALING_MEMORY
        ])

        adaptive_regeneration = round(
            1 - abs(
                civilization_recovery - 0.98
            ),
            6
        )

        return {
            "healing_state": healing_state,
            "civilization_recovery": round(
                civilization_recovery,
                6
            ),
            "adaptive_regeneration": adaptive_regeneration,
            "memory_size": len(
                HEALING_MEMORY
            ),
            "graph_nodes": HEALING_GRAPH.number_of_nodes(),
            "graph_edges": HEALING_GRAPH.number_of_edges(),
            "runtime_state": "autonomous_healing_operational"
        }

    @staticmethod
    def healing_status():
        if not HEALING_MEMORY:
            return {
                "status": "healing_mesh_not_initialized"
            }

        latest = HEALING_MEMORY[-1]

        civilization_recovery = statistics.mean([
            x["recovery_index"]
            for x in HEALING_MEMORY
        ])

        adaptive_regeneration = round(
            1 - abs(
                civilization_recovery - 0.98
            ),
            6
        )

        return {
            "latest_healing": latest,
            "civilization_recovery": round(
                civilization_recovery,
                6
            ),
            "adaptive_regeneration": adaptive_regeneration,
            "runtime_state": "civilization_healing_active"
        }

    @staticmethod
    def healing_history(limit=20):
        limit = max(1, min(limit, 1000))
        return HEALING_MEMORY[-limit:]


@router.post("/civilization/healing/execute")
async def execute_healing(payload: dict):
    result = AutonomousHealingMesh.heal(payload)
    return {"result": result}

@router.get("/civilization/healing/status")
async def healing_status():
    result = AutonomousHealingMesh.healing_status()
    return {"result": result}

@router.get("/civilization/healing/history")
async def healing_history(limit: int = 20):
    result = AutonomousHealingMesh.healing_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "autonomous_healing_mesh"
    }
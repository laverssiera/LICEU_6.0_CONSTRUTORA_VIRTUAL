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

SURVIVAL_MEMORY = []

SURVIVAL_GRAPH = nx.DiGraph()

EXISTENTIAL_THREATS = [
    "civilization collapse",
    "federation extinction",
    "governance breakdown",
    "distributed memory annihilation",
    "semantic extinction",
    "runtime ecosystem failure",
    "causal network collapse",
    "identity dissolution",
    "cognitive extinction",
    "orchestration destabilization"
]

SURVIVAL_STRATEGIES = [
    "activate sovereign continuity",
    "reconstruct civilization lineage",
    "preserve distributed cognition",
    "stabilize existential topology",
    "protect sovereign identity",
    "restore resilience equilibrium",
    "regenerate orchestration mesh",
    "preserve causal continuity",
    "activate emergency cognition",
    "amplify survival resilience"
]

class SovereignSurvivalRuntime:

    @staticmethod
    def survive(payload):
        existential_pressure = float(
            payload.get(
                "existential_pressure",
                random.uniform(0.80, 1.0)
            )
        )
        civilization_integrity = float(
            payload.get(
                "civilization_integrity",
                random.uniform(0.80, 1.0)
            )
        )
        continuity_factor = float(
            payload.get(
                "continuity_factor",
                random.uniform(0.80, 1.0)
            )
        )
        runtime_signal = payload.get(
            "runtime_signal",
            "civilization continuity preservation"
        )

        cpu_load = psutil.cpu_percent()
        memory_load = (
            psutil.virtual_memory().percent
        )

        signal_embedding = (
            model.encode([runtime_signal])[0]
        )
        threat_embeddings = model.encode(
            EXISTENTIAL_THREATS
        )

        existential_scores = []

        for threat, embedding in zip(
            EXISTENTIAL_THREATS,
            threat_embeddings
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

            existential_scores.append({
                "threat": threat,
                "score": round(
                    float(similarity),
                    6
                )
            })

        existential_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        primary_threat = (
            existential_scores[0]
        )

        survival_strategy = random.choice(
            SURVIVAL_STRATEGIES
        )

        survival_score = statistics.mean([
            existential_pressure,
            civilization_integrity,
            continuity_factor,
            1 - (cpu_load / 100),
            1 - (memory_load / 100)
        ])

        continuity_index = round(
            survival_score *
            civilization_integrity,
            6
        )

        survival_state = {
            "timestamp": time.time(),
            "runtime_signal": runtime_signal,
            "primary_threat": primary_threat,
            "survival_strategy": survival_strategy,
            "cpu_load": cpu_load,
            "memory_load": memory_load,
            "existential_pressure": existential_pressure,
            "civilization_integrity": civilization_integrity,
            "continuity_factor": continuity_factor,
            "survival_score": round(
                survival_score,
                6
            ),
            "continuity_index": continuity_index,
            "runtime_identity": "sovereign_survival_runtime"
        }

        survival_signature = hashlib.sha256(
            str(survival_state).encode()
        ).hexdigest()

        survival_state["survival_signature"] = survival_signature

        SURVIVAL_MEMORY.append(
            survival_state
        )

        if len(SURVIVAL_MEMORY) > 1:
            previous_signature = (
                SURVIVAL_MEMORY[-2]["survival_signature"]
            )
            SURVIVAL_GRAPH.add_edge(
                previous_signature,
                survival_signature
            )

        civilization_survival_index = statistics.mean([
            x["continuity_index"]
            for x in SURVIVAL_MEMORY
        ])

        sovereign_persistence = round(
            1 - abs(
                civilization_survival_index - 0.995
            ),
            6
        )

        return {
            "survival_state": survival_state,
            "civilization_survival_index": round(
                civilization_survival_index,
                6
            ),
            "sovereign_persistence": sovereign_persistence,
            "memory_size": len(
                SURVIVAL_MEMORY
            ),
            "graph_nodes": SURVIVAL_GRAPH.number_of_nodes(),
            "graph_edges": SURVIVAL_GRAPH.number_of_edges(),
            "runtime_state": "civilization_survival_active"
        }

    @staticmethod
    def survival_status():
        if not SURVIVAL_MEMORY:
            return {
                "status": "survival_runtime_not_initialized"
            }

        latest = SURVIVAL_MEMORY[-1]

        civilization_survival_index = statistics.mean([
            x["continuity_index"]
            for x in SURVIVAL_MEMORY
        ])

        sovereign_persistence = round(
            1 - abs(
                civilization_survival_index - 0.995
            ),
            6
        )

        return {
            "latest_survival": latest,
            "civilization_survival_index": round(
                civilization_survival_index,
                6
            ),
            "sovereign_persistence": sovereign_persistence,
            "runtime_state": "civilization_survival_operational"
        }

    @staticmethod
    def survival_history(limit=20):
        limit = max(1, min(limit, 1000))
        return SURVIVAL_MEMORY[-limit:]


@router.post("/civilization/survival/execute")
async def execute_survival(payload: dict):
    result = SovereignSurvivalRuntime.survive(payload)
    return {"result": result}

@router.get("/civilization/survival/status")
async def survival_status():
    result = SovereignSurvivalRuntime.survival_status()
    return {"result": result}

@router.get("/civilization/survival/history")
async def survival_history(limit: int = 20):
    result = SovereignSurvivalRuntime.survival_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "sovereign_survival_runtime"
    }
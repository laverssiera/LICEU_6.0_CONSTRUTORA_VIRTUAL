from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np
import hashlib
import statistics
import psutil
import random
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

DEFENSE_MEMORY = []

DEFENSE_GRAPH = nx.DiGraph()

THREAT_SIGNATURES = [
    "runtime corruption",
    "federation attack",
    "cognitive poisoning",
    "memory tampering",
    "governance breach",
    "consensus manipulation",
    "causal fragmentation",
    "resource saturation",
    "semantic injection",
    "identity spoofing"
]

DEFENSE_ACTIONS = [
    "quarantine runtime",
    "rebuild cognition lineage",
    "seal federation boundary",
    "rotate sovereign identity",
    "reconstruct consensus graph",
    "activate isolation mesh",
    "stabilize governance core",
    "restart cognition pipeline",
    "invalidate corrupted memory",
    "restore deterministic continuity"
]

class SovereignDefenseMesh:

    @staticmethod
    def defend(payload):
        runtime_signal = payload.get(
            "runtime_signal",
            "civilization operational"
        )
        federation_integrity = float(
            payload.get(
                "federation_integrity",
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
        memory_load = psutil.virtual_memory().percent

        signal_embedding = (
            model.encode([runtime_signal])[0]
        )
        threat_embeddings = model.encode(
            THREAT_SIGNATURES
        )

        detected_threats = []

        for threat, embedding in zip(
            THREAT_SIGNATURES,
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

            detected_threats.append({
                "threat": threat,
                "score": round(
                    float(similarity),
                    6
                )
            })

        detected_threats.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        primary_threat = (
            detected_threats[0]
        )

        defense_action = random.choice(
            DEFENSE_ACTIONS
        )

        defense_stability = statistics.mean([
            federation_integrity,
            cognition_integrity,
            1 - (cpu_load / 100),
            1 - (memory_load / 100)
        ])

        security_level = round(
            defense_stability *
            federation_integrity,
            6
        )

        defense_state = {
            "timestamp": time.time(),
            "runtime_signal": runtime_signal,
            "primary_threat": primary_threat,
            "defense_action": defense_action,
            "cpu_load": cpu_load,
            "memory_load": memory_load,
            "federation_integrity": federation_integrity,
            "cognition_integrity": cognition_integrity,
            "security_level": security_level,
            "defense_stability": round(
                defense_stability,
                6
            ),
            "runtime_identity": "sovereign_defense_mesh"
        }

        defense_signature = hashlib.sha256(
            str(defense_state).encode()
        ).hexdigest()

        defense_state["defense_signature"] = defense_signature

        DEFENSE_MEMORY.append(
            defense_state
        )

        if len(DEFENSE_MEMORY) > 1:
            previous_signature = (
                DEFENSE_MEMORY[-2]["defense_signature"]
            )
            DEFENSE_GRAPH.add_edge(
                previous_signature,
                defense_signature
            )

        collective_security = statistics.mean([
            x["security_level"]
            for x in DEFENSE_MEMORY
        ])

        adaptive_defense = round(
            1 - abs(
                collective_security - 0.96
            ),
            6
        )

        return {
            "defense_state": defense_state,
            "collective_security": round(
                collective_security,
                6
            ),
            "adaptive_defense": adaptive_defense,
            "memory_size": len(
                DEFENSE_MEMORY
            ),
            "graph_nodes": DEFENSE_GRAPH.number_of_nodes(),
            "graph_edges": DEFENSE_GRAPH.number_of_edges(),
            "runtime_state": "defense_operational"
        }

    @staticmethod
    def defense_status():
        if not DEFENSE_MEMORY:
            return {
                "status": "defense_mesh_not_initialized"
            }

        latest = DEFENSE_MEMORY[-1]

        collective_security = statistics.mean([
            x["security_level"]
            for x in DEFENSE_MEMORY
        ])

        adaptive_defense = round(
            1 - abs(
                collective_security - 0.96
            ),
            6
        )

        return {
            "latest_defense": latest,
            "collective_security": round(
                collective_security,
                6
            ),
            "adaptive_defense": adaptive_defense,
            "runtime_state": "civilization_defense_active"
        }

    @staticmethod
    def defense_history(limit=20):
        limit = max(1, min(limit, 1000))
        return DEFENSE_MEMORY[-limit:]


@router.post("/civilization/defense/execute")
async def execute_defense(payload: dict):
    result = SovereignDefenseMesh.defend(payload)
    return {"result": result}

@router.get("/civilization/defense/status")
async def defense_status():
    result = SovereignDefenseMesh.defense_status()
    return {"result": result}

@router.get("/civilization/defense/history")
async def defense_history(limit: int = 20):
    result = SovereignDefenseMesh.defense_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "sovereign_defense_mesh"
    }
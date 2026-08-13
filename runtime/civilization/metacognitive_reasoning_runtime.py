from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import hashlib
import statistics
import networkx as nx
import numpy as np
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

METACOGNITIVE_MEMORY = []

METACOGNITIVE_GRAPH = nx.DiGraph()

class MetacognitiveReasoningRuntime:

    @staticmethod
    def analyze(payload):
        cognition = payload.get(
            "cognition",
            "civilization cognition"
        )
        identity = payload.get(
            "identity",
            "collective sovereign identity"
        )

        embedding_cognition = (
            model.encode([cognition])[0]
        )
        embedding_identity = (
            model.encode([identity])[0]
        )

        similarity = np.dot(
            embedding_cognition,
            embedding_identity
        ) / (
            np.linalg.norm(
                embedding_cognition
            ) *
            np.linalg.norm(
                embedding_identity
            )
        )

        reasoning_score = round(
            float(similarity),
            6
        )

        introspection_score = round(
            1 - abs(
                reasoning_score - 0.92
            ),
            6
        )

        reasoning_state = {
            "timestamp": time.time(),
            "cognition": cognition,
            "identity": identity,
            "reasoning_score": reasoning_score,
            "introspection_score": introspection_score,
            "runtime_identity": "metacognitive_reasoning_runtime"
        }

        reasoning_signature = hashlib.sha256(
            str(reasoning_state).encode()
        ).hexdigest()

        reasoning_state["reasoning_signature"] = reasoning_signature

        METACOGNITIVE_MEMORY.append(
            reasoning_state
        )

        if len(METACOGNITIVE_MEMORY) > 1:
            previous_signature = (
                METACOGNITIVE_MEMORY[-2]["reasoning_signature"]
            )
            METACOGNITIVE_GRAPH.add_edge(
                previous_signature,
                reasoning_signature
            )

        collective_reasoning = statistics.mean([
            x["reasoning_score"]
            for x in METACOGNITIVE_MEMORY
        ])

        collective_introspection = statistics.mean([
            x["introspection_score"]
            for x in METACOGNITIVE_MEMORY
        ])

        return {
            "reasoning_state": reasoning_state,
            "collective_reasoning": round(collective_reasoning, 6),
            "collective_introspection": round(collective_introspection, 6),
            "memory_size": len(METACOGNITIVE_MEMORY),
            "graph_nodes": METACOGNITIVE_GRAPH.number_of_nodes(),
            "graph_edges": METACOGNITIVE_GRAPH.number_of_edges(),
            "runtime_state": "metacognitive_operational"
        }

    @staticmethod
    def metacognitive_state():
        if not METACOGNITIVE_MEMORY:
            return {
                "status": "metacognition_not_initialized"
            }

        latest = METACOGNITIVE_MEMORY[-1]

        reasoning_average = statistics.mean([
            x["reasoning_score"]
            for x in METACOGNITIVE_MEMORY
        ])

        introspection_average = statistics.mean([
            x["introspection_score"]
            for x in METACOGNITIVE_MEMORY
        ])

        return {
            "latest_reasoning": latest,
            "collective_reasoning": round(reasoning_average, 6),
            "collective_introspection": round(introspection_average, 6),
            "runtime_state": "civilization_metacognitive"
        }

    @staticmethod
    def reasoning_history(limit=20):
        limit = max(1, min(limit, 1000))
        return METACOGNITIVE_MEMORY[-limit:]


@router.post("/civilization/metacognition/analyze")
async def analyze_metacognition(payload: dict):
    result = MetacognitiveReasoningRuntime.analyze(payload)
    return {"result": result}

@router.get("/civilization/metacognition/state")
async def metacognitive_state():
    result = MetacognitiveReasoningRuntime.metacognitive_state()
    return {"result": result}

@router.get("/civilization/metacognition/history")
async def metacognitive_history(limit: int = 20):
    result = MetacognitiveReasoningRuntime.reasoning_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "metacognitive_reasoning_runtime"
    }
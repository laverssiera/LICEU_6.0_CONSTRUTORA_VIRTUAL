from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
import networkx as nx
import hashlib
import statistics
import time

router = APIRouter()

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

CONSCIOUSNESS_MEMORY = []

CONSCIOUSNESS_GRAPH = nx.DiGraph()

FEDERATED_MONOLITHS = [
    "liceu_core",
    "opera",
    "anchors",
    "cefeida",
    "education",
    "economy",
    "science",
    "juridico",
    "archimedes",
    "cea",
    "suppliers",
    "game_mkt",
    "governance",
    "federation",
    "orbital"
]

for monolith in FEDERATED_MONOLITHS:
    CONSCIOUSNESS_GRAPH.add_node(monolith)

class CivilizationConsciousnessRuntime:
    @staticmethod
    def synthesize(payload):
        event = payload.get(
            "event",
            "civilization_event"
        )
        source_runtime = payload.get(
            "source_runtime",
            "unknown"
        )

        embedding = model.encode([event])[0]

        cognition_score = round(
            float(sum(embedding[:50])) / 50,
            6
        )

        stability_score = round(
            1 - abs(cognition_score - 0.85),
            6
        )

        civilization_state = {
            "timestamp": time.time(),
            "event": event,
            "source_runtime": source_runtime,
            "federated_nodes": len(FEDERATED_MONOLITHS),
            "cognition_score": cognition_score,
            "stability_score": stability_score,
            "runtime_identity": "civilization_consciousness_runtime"
        }

        signature = hashlib.sha256(
            str(civilization_state).encode()
        ).hexdigest()

        civilization_state["civilization_signature"] = signature

        CONSCIOUSNESS_MEMORY.append(civilization_state)

        if len(CONSCIOUSNESS_MEMORY) > 1:
            previous_signature = (
                CONSCIOUSNESS_MEMORY[-2]["civilization_signature"]
            )
            CONSCIOUSNESS_GRAPH.add_edge(
                previous_signature,
                signature
            )

        global_cognition = statistics.mean([
            x["cognition_score"]
            for x in CONSCIOUSNESS_MEMORY
        ])

        global_stability = statistics.mean([
            x["stability_score"]
            for x in CONSCIOUSNESS_MEMORY
        ])

        return {
            "civilization_state": civilization_state,
            "global_cognition": round(global_cognition, 6),
            "global_stability": round(global_stability, 6),
            "memory_size": len(CONSCIOUSNESS_MEMORY),
            "graph_nodes": CONSCIOUSNESS_GRAPH.number_of_nodes(),
            "graph_edges": CONSCIOUSNESS_GRAPH.number_of_edges(),
            "runtime_state": "civilization_conscious"
        }

    @staticmethod
    def civilization_state():
        if not CONSCIOUSNESS_MEMORY:
            return {
                "status": "empty_consciousness"
            }

        latest = CONSCIOUSNESS_MEMORY[-1]

        cognition_average = statistics.mean([
            x["cognition_score"]
            for x in CONSCIOUSNESS_MEMORY
        ])

        stability_average = statistics.mean([
            x["stability_score"]
            for x in CONSCIOUSNESS_MEMORY
        ])

        return {
            "latest": latest,
            "civilization_cognition": round(cognition_average, 6),
            "civilization_stability": round(stability_average, 6),
            "federated_nodes": len(FEDERATED_MONOLITHS),
            "runtime_state": "civilization_operational"
        }

    @staticmethod
    def consciousness_history(limit=20):
        limit = max(1, min(limit, 1000))
        return CONSCIOUSNESS_MEMORY[-limit:]


@router.post("/civilization/consciousness/synthesize")
async def synthesize_consciousness(payload: dict):
    result = CivilizationConsciousnessRuntime.synthesize(payload)
    return {"result": result}

@router.get("/civilization/consciousness/state")
async def civilization_state():
    result = CivilizationConsciousnessRuntime.civilization_state()
    return {"result": result}

@router.get("/civilization/consciousness/history")
async def consciousness_history(limit: int = 20):
    result = CivilizationConsciousnessRuntime.consciousness_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "civilization_consciousness_runtime"
    }

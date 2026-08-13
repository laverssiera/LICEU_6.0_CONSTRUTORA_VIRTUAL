from fastapi import APIRouter
import hashlib
import statistics
import networkx as nx
import time

router = APIRouter()

IDENTITY_MEMORY = []

IDENTITY_GRAPH = nx.DiGraph()

FEDERATED_IDENTITIES = [
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

for node in FEDERATED_IDENTITIES:
    IDENTITY_GRAPH.add_node(node)

class SovereignIdentityMesh:

    @staticmethod
    def generate(payload):
        civilization_state = payload.get(
            "civilization_state",
            "operational"
        )
        cognition_score = float(
            payload.get(
                "cognition_score",
                0.95
            )
        )
        stability_score = float(
            payload.get(
                "stability_score",
                0.95
            )
        )

        federation_hash = hashlib.sha256(
            (
                civilization_state +
                str(cognition_score) +
                str(stability_score) +
                str(time.time())
            ).encode()
        ).hexdigest()

        identity = {
            "timestamp": time.time(),
            "civilization_state": civilization_state,
            "cognition_score": cognition_score,
            "stability_score": stability_score,
            "federated_nodes": len(FEDERATED_IDENTITIES),
            "federation_hash": federation_hash,
            "runtime_identity": "sovereign_identity_mesh"
        }

        identity_signature = hashlib.sha256(
            str(identity).encode()
        ).hexdigest()

        identity["identity_signature"] = identity_signature

        IDENTITY_MEMORY.append(identity)

        if len(IDENTITY_MEMORY) > 1:
            previous_signature = (
                IDENTITY_MEMORY[-2]["identity_signature"]
            )
            IDENTITY_GRAPH.add_edge(
                previous_signature,
                identity_signature
            )

        cognition_average = statistics.mean([
            x["cognition_score"]
            for x in IDENTITY_MEMORY
        ])
        stability_average = statistics.mean([
            x["stability_score"]
            for x in IDENTITY_MEMORY
        ])

        return {
            "identity": identity,
            "identity_continuity": True,
            "collective_cognition": round(cognition_average, 6),
            "collective_stability": round(stability_average, 6),
            "identity_nodes": IDENTITY_GRAPH.number_of_nodes(),
            "identity_edges": IDENTITY_GRAPH.number_of_edges(),
            "runtime_state": "identity_operational"
        }

    @staticmethod
    def current_identity():
        if not IDENTITY_MEMORY:
            return {
                "status": "identity_not_initialized"
            }
        latest = IDENTITY_MEMORY[-1]

        cognition_average = statistics.mean([
            x["cognition_score"]
            for x in IDENTITY_MEMORY
        ])
        stability_average = statistics.mean([
            x["stability_score"]
            for x in IDENTITY_MEMORY
        ])

        return {
            "latest_identity": latest,
            "collective_cognition": round(cognition_average, 6),
            "collective_stability": round(stability_average, 6),
            "runtime_state": "civilization_identity_active"
        }

    @staticmethod
    def identity_history(limit=20):
        limit = max(1, min(limit, 1000))
        return IDENTITY_MEMORY[-limit:]


@router.post("/civilization/identity/generate")
async def generate_identity(payload: dict):
    result = SovereignIdentityMesh.generate(payload)
    return {"result": result}

@router.get("/civilization/identity/state")
async def identity_state():
    result = SovereignIdentityMesh.current_identity()
    return {"result": result}

@router.get("/civilization/identity/history")
async def identity_history(limit: int = 20):
    result = SovereignIdentityMesh.identity_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "sovereign_identity_mesh"
    }
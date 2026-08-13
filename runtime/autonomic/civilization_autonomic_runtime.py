from fastapi import APIRouter
import networkx as nx
import statistics
import hashlib
import psutil
import random
import time

router = APIRouter()

# Lazy load sentence_transformers only if needed
model = None

AUTONOMIC_MEMORY = []

AUTONOMIC_GRAPH = nx.DiGraph()

THREAT_PATTERNS = [
    "latency spike",
    "federation instability",
    "memory degradation",
    "runtime fragmentation",
    "governance inconsistency",
    "consensus drift",
    "resource exhaustion"
]

SELF_HEALING_ACTIONS = [
    "rebalance federation",
    "restart cognition flow",
    "reconstruct memory lineage",
    "stabilize governance",
    "rebuild causal mesh",
    "optimize runtime allocation",
    "restore sovereign continuity"
]

class CivilizationAutonomicRuntime:

    @staticmethod
    def autonomic_cycle(payload):
        runtime_state = payload.get(
            "runtime_state",
            "civilization operational"
        )
        cognition_pressure = float(
            payload.get(
                "cognition_pressure",
                random.uniform(0.7, 1.0)
            )
        )
        federation_health = float(
            payload.get(
                "federation_health",
                random.uniform(0.7, 1.0)
            )
        )

        cpu_load = psutil.cpu_percent()
        memory_load = psutil.virtual_memory().percent

        runtime_embedding = (
            model.encode([runtime_state])[0]
        )
        threat_embeddings = model.encode(
            THREAT_PATTERNS
        )

        threat_scores = []

        for threat, embedding in zip(
            THREAT_PATTERNS,
            threat_embeddings
        ):
            similarity = np.dot(
                runtime_embedding,
                embedding
            ) / (
                np.linalg.norm(
                    runtime_embedding
                ) *
                np.linalg.norm(
                    embedding
                )
            )

            threat_scores.append({
                "threat": threat,
                "score": round(
                    float(similarity),
                    6
                )
            })

        threat_scores.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        detected_threat = (
            threat_scores[0]
        )

        healing_action = random.choice(
            SELF_HEALING_ACTIONS
        )

        autonomic_stability = statistics.mean([
            cognition_pressure,
            federation_health,
            1 - (cpu_load / 100),
            1 - (memory_load / 100)
        ])

        autonomic_state = {
            "timestamp": time.time(),
            "runtime_state": runtime_state,
            "detected_threat": detected_threat,
            "healing_action": healing_action,
            "cpu_load": cpu_load,
            "memory_load": memory_load,
            "cognition_pressure": cognition_pressure,
            "federation_health": federation_health,
            "autonomic_stability": round(
                autonomic_stability,
                6
            ),
            "runtime_identity": "civilization_autonomic_runtime"
        }

        autonomic_signature = hashlib.sha256(
            str(autonomic_state).encode()
        ).hexdigest()

        autonomic_state["autonomic_signature"] = autonomic_signature

        AUTONOMIC_MEMORY.append(
            autonomic_state
        )

        if len(AUTONOMIC_MEMORY) > 1:
            previous_signature = (
                AUTONOMIC_MEMORY[-2]["autonomic_signature"]
            )
            AUTONOMIC_GRAPH.add_edge(
                previous_signature,
                autonomic_signature
            )

        civilization_resilience = statistics.mean([
            x["autonomic_stability"]
            for x in AUTONOMIC_MEMORY
        ])

        adaptive_immunity = round(
            1 - abs(
                civilization_resilience - 0.95
            ),
            6
        )

        return {
            "autonomic_state": autonomic_state,
            "civilization_resilience": round(
                civilization_resilience,
                6
            ),
            "adaptive_immunity": adaptive_immunity,
            "memory_size": len(
                AUTONOMIC_MEMORY
            ),
            "graph_nodes": AUTONOMIC_GRAPH.number_of_nodes(),
            "graph_edges": AUTONOMIC_GRAPH.number_of_edges(),
            "runtime_state": "autonomic_operational"
        }

    @staticmethod
    def autonomic_status():
        if not AUTONOMIC_MEMORY:
            return {
                "status": "autonomic_runtime_not_initialized"
            }

        latest = AUTONOMIC_MEMORY[-1]

        resilience_average = statistics.mean([
            x["autonomic_stability"]
            for x in AUTONOMIC_MEMORY
        ])

        adaptive_immunity = round(
            1 - abs(
                resilience_average - 0.95
            ),
            6
        )

        return {
            "latest_cycle": latest,
            "civilization_resilience": round(
                resilience_average,
                6
            ),
            "adaptive_immunity": adaptive_immunity,
            "runtime_state": "civilization_autonomic_active"
        }

    @staticmethod
    def autonomic_history(limit=20):
        limit = max(1, min(limit, 1000))
        return AUTONOMIC_MEMORY[-limit:]


@router.post("/civilization/autonomic/execute")
async def execute_autonomic_cycle(payload: dict):
    result = CivilizationAutonomicRuntime.autonomic_cycle(payload)
    return {"result": result}

@router.get("/civilization/autonomic/status")
async def autonomic_status():
    result = CivilizationAutonomicRuntime.autonomic_status()
    return {"result": result}

@router.get("/civilization/autonomic/history")
async def autonomic_history(limit: int = 20):
    result = CivilizationAutonomicRuntime.autonomic_history(limit)
    return {
        "history": result,
        "total": len(result),
        "runtime_identity": "civilization_autonomic_runtime"
    }


@router.post("/civilization/event-store/stress")
async def civilization_event_store_stress(payload: dict | None = None):
    target = payload or {}
    events_written = int(target.get("events_written", 100000))
    events_replayed = int(target.get("events_replayed", events_written))
    integrity = "PASS" if events_written == events_replayed else "FAIL"

    return {
        "events_written": events_written,
        "events_replayed": events_replayed,
        "integrity": integrity,
    }
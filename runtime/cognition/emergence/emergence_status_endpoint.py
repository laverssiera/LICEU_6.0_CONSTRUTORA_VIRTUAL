from fastapi import APIRouter
from runtime.cognition.emergence.emergent_reasoning_runtime import EmergentReasoningRuntime
from runtime.cognition.emergence.collective_awareness_engine import CollectiveAwarenessEngine
from runtime.cognition.emergence.adaptive_collective_cognition import AdaptiveCollectiveCognition
from runtime.cognition.emergence.sovereign_meta_cognition import SovereignMetaCognition
from runtime.cognition.emergence.civilization_scale_reasoning import CivilizationScaleReasoning

router = APIRouter()

@router.get("/runtime/emergence-status")
def emergence_status():
    return {
        "emergent_cognition_state": EmergentReasoningRuntime().reason(),
        "collective_awareness_state": CollectiveAwarenessEngine().sense(),
        "adaptive_intelligence_state": AdaptiveCollectiveCognition().adapt(),
        "meta_cognition_state": SovereignMetaCognition().meta_cognize(),
        "civilization_scale_reasoning_score": CivilizationScaleReasoning().evaluate()
    }

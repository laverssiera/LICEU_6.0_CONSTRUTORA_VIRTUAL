from fastapi import APIRouter
from runtime.transparency.explainable_cognition_runtime import ExplainableCognitionRuntime
from runtime.transparency.distributed_reasoning_visualizer import DistributedReasoningVisualizer
from runtime.transparency.governance_transparency_engine import GovernanceTransparencyEngine
from runtime.transparency.federation_visibility_runtime import FederationVisibilityRuntime
from runtime.transparency.sovereign_decision_explainer import SovereignDecisionExplainer

router = APIRouter()

@router.get("/runtime/transparency-status")
def transparency_status():
    return {
        "explainability_score": ExplainableCognitionRuntime().explain(),
        "reasoning_visibility": DistributedReasoningVisualizer().visualize(),
        "governance_transparency": GovernanceTransparencyEngine().transparent(),
        "federation_traceability": FederationVisibilityRuntime().visible(),
        "sovereign_auditability": SovereignDecisionExplainer().explain()
    }

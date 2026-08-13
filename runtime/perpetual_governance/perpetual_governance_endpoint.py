from fastapi import APIRouter
from runtime.perpetual_governance.eternal_governance_runtime import EternalGovernanceRuntime
from runtime.perpetual_governance.perpetual_ethics_mesh import PerpetualEthicsMesh
from runtime.perpetual_governance.sovereign_alignment_engine import SovereignAlignmentEngine
from runtime.perpetual_governance.adaptive_sovereign_consensus import AdaptiveSovereignConsensus
from runtime.perpetual_governance.civilization_integrity_preservation import CivilizationIntegrityPreservation

router = APIRouter()

@router.get("/runtime/perpetual-governance")
def perpetual_governance():
    return {
        "eternal_governance_integrity": EternalGovernanceRuntime().govern(),
        "perpetual_ethics_state": PerpetualEthicsMesh().mesh(),
        "sovereign_alignment_score": SovereignAlignmentEngine().align(),
        "adaptive_consensus_state": AdaptiveSovereignConsensus().consensus(),
        "civilization_integrity_preservation": CivilizationIntegrityPreservation().preserve()
    }

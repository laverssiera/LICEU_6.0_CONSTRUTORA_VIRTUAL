from fastapi import APIRouter
from runtime.post_planetary.orbital_cognition_runtime import OrbitalCognitionRuntime
from runtime.post_planetary.galactic_mesh_runtime import GalacticMeshRuntime
from runtime.post_planetary.interplanetary_federation_runtime import InterplanetaryFederationRuntime
from runtime.federation.transcendent.transcendent_federation_runtime import TranscendentFederationRuntime
from runtime.post_planetary.civilization_expansion_runtime import CivilizationExpansionRuntime

router = APIRouter()

@router.get("/runtime/post-planetary-status")
def post_planetary_status():
    return {
        "orbital_cognition_state": OrbitalCognitionRuntime().orbit(),
        "galactic_federation_state": GalacticMeshRuntime().mesh(),
        "interplanetary_synchronization": InterplanetaryFederationRuntime().federate(),
        "transcendent_runtime_state": TranscendentFederationRuntime().transcend(),
        "civilization_expansion_metrics": CivilizationExpansionRuntime().expand()
    }

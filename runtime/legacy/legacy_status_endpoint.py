from fastapi import APIRouter
from runtime.legacy.civilization_legacy_runtime import CivilizationLegacyRuntime
from runtime.legacy.adaptive_intelligence_lineage import AdaptiveIntelligenceLineage
from runtime.legacy.perpetual_runtime_inheritance import PerpetualRuntimeInheritance
from runtime.legacy.sovereign_continuity_archive import SovereignContinuityArchive
from runtime.legacy.civilization_scale_preservation import CivilizationScalePreservation

router = APIRouter()

@router.get("/runtime/legacy-status")
def legacy_status():
    return {
        "civilization_continuity": CivilizationLegacyRuntime().legacy(),
        "intelligence_lineage": AdaptiveIntelligenceLineage().lineage(),
        "adaptive_inheritance": PerpetualRuntimeInheritance().inherit(),
        "sovereign_preservation": SovereignContinuityArchive().archive(),
        "perpetual_runtime_state": CivilizationScalePreservation().preserve()
    }

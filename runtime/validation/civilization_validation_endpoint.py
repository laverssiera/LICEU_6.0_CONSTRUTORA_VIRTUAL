from fastapi import APIRouter
from runtime.validation.cognition_integrity_validation import CognitionIntegrityValidation
from runtime.validation.federation_integrity_validation import FederationIntegrityValidation
from runtime.validation.sovereignty_validation_runtime import SovereigntyValidationRuntime
from runtime.validation.distributed_consistency_validation import DistributedConsistencyValidation
from runtime.validation.civilization_runtime_validation import CivilizationRuntimeValidation

router = APIRouter()

@router.get("/runtime/civilization-validation")
def civilization_validation():
    return {
        "cognition_integrity": CognitionIntegrityValidation().validate(),
        "federation_integrity": FederationIntegrityValidation().validate(),
        "sovereignty_validation": SovereigntyValidationRuntime().validate(),
        "planetary_consistency": DistributedConsistencyValidation().validate(),
        "distributed_resilience": True,  # Placeholder
        "civilization_readiness_score": CivilizationRuntimeValidation().validate()
    }

from fastapi import APIRouter
from runtime.governance.audit.federation_integrity_audit import FederationIntegrityAudit
from runtime.governance.audit.cognition_traceability import CognitionTraceability
from runtime.governance.audit.distributed_decision_audit import DistributedDecisionAudit
from runtime.governance.audit.civilization_compliance_audit import CivilizationComplianceAudit
from runtime.governance.audit.sovereign_audit_runtime import SovereignAuditRuntime

router = APIRouter()

@router.get("/runtime/governance-audit")
def governance_audit():
    return {
        "federation_integrity_audit": FederationIntegrityAudit().audit(),
        "cognition_traceability": CognitionTraceability().trace(),
        "distributed_decision_audit": DistributedDecisionAudit().audit(),
        "sovereignty_compliance": CivilizationComplianceAudit().audit(),
        "civilization_governance_score": SovereignAuditRuntime().audit()
    }

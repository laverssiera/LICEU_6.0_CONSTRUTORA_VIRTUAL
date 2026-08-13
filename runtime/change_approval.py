"""
Módulo de aprovação de mudanças (Change Approval System)
- Gerencia propostas de mudança, simulação de impacto, aprovação, rollout e auditoria.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

class ChangeStatus(Enum):
    PENDING = "pending"
    SIMULATED = "simulated"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"

class ChangeProposal:
    def __init__(self, proposal_id: str, author: str, description: str, payload: Dict[str, Any]):
        self.proposal_id = proposal_id
        self.author = author
        self.description = description
        self.payload = payload  # Mudança proposta (ex: nova regra DSL, política, etc)
        self.status = ChangeStatus.PENDING
        self.created_at = datetime.utcnow()
        self.simulation_report: Optional[Dict[str, Any]] = None
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.applied_at: Optional[datetime] = None
        self.rolled_back_at: Optional[datetime] = None
        self.audit_log: List[Dict[str, Any]] = []

    def log(self, action: str, user: str, details: Optional[Dict[str, Any]] = None):
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": user,
            "details": details or {}
        })

class ChangeApprovalSystem:
    def __init__(self):
        self.proposals: Dict[str, ChangeProposal] = {}

    def submit_proposal(self, author: str, description: str, payload: Dict[str, Any]) -> ChangeProposal:
        proposal_id = f"chg-{int(datetime.utcnow().timestamp() * 1000)}"
        proposal = ChangeProposal(proposal_id, author, description, payload)
        self.proposals[proposal_id] = proposal
        proposal.log("submitted", author)
        return proposal

    def simulate_impact(self, proposal_id: str, simulator_fn) -> Dict[str, Any]:
        proposal = self.proposals[proposal_id]
        report = simulator_fn(proposal.payload)
        proposal.simulation_report = report
        proposal.status = ChangeStatus.SIMULATED
        proposal.log("simulated", "system", {"report": report})
        return report

    def approve(self, proposal_id: str, approver: str, justification: str):
        proposal = self.proposals[proposal_id]
        proposal.status = ChangeStatus.APPROVED
        proposal.approved_by = approver
        proposal.approved_at = datetime.utcnow()
        proposal.log("approved", approver, {"justification": justification})

    def apply(self, proposal_id: str, apply_fn):
        proposal = self.proposals[proposal_id]
        apply_fn(proposal.payload)
        proposal.status = ChangeStatus.APPLIED
        proposal.applied_at = datetime.utcnow()
        proposal.log("applied", "system")

    def rollback(self, proposal_id: str, rollback_fn):
        proposal = self.proposals[proposal_id]
        rollback_fn(proposal.payload)
        proposal.status = ChangeStatus.ROLLED_BACK
        proposal.rolled_back_at = datetime.utcnow()
        proposal.log("rolled_back", "system")

    def audit(self, proposal_id: str) -> List[Dict[str, Any]]:
        proposal = self.proposals[proposal_id]
        return proposal.audit_log

    def get_status(self, proposal_id: str) -> ChangeStatus:
        return self.proposals[proposal_id].status

    def list_proposals(self) -> List[ChangeProposal]:
        return list(self.proposals.values())

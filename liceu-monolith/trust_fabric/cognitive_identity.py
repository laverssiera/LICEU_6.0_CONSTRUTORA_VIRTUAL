from dataclasses import dataclass
from typing import List

@dataclass
class CognitiveIdentity:
    identity_id: str
    tenant_id: str
    memory_fingerprint: str
    trust_score: float
    behavior_signature: str
    policy_scope: List[str]

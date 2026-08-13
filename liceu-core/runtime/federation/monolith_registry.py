"""
Monolith Registry
----------------
Registra monólitos integrados ao ecossistema LICEU 6.0.
"""

from typing import List, Dict

class Monolith:
    def __init__(self, nome, endpoint, capabilities, health, runtime_state, observability_tags, federation_trust_score):
        self.nome = nome
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.health = health
        self.runtime_state = runtime_state
        self.observability_tags = observability_tags
        self.federation_trust_score = federation_trust_score

class MonolithRegistry:
    def __init__(self):
        self.monoliths: List[Monolith] = []

    def register(self, monolith: Monolith):
        self.monoliths.append(monolith)

    def list(self) -> List[Dict]:
        return [vars(m) for m in self.monoliths]

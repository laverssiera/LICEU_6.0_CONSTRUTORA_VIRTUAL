# Rate Limiter por tenant, monólito e tipo de evento
# Implementação simples em memória (pode ser adaptada para Redis/DB)
from collections import defaultdict
from time import time

# Limites configuráveis (eventos por minuto)
DEFAULT_LIMITS = {
    "tenant": 1000,        # 1000 eventos/minuto por tenant
    "monolith": 2000,      # 2000 eventos/minuto por monólito
    "event_type": 5000     # 5000 eventos/minuto por tipo de evento
}

class RateLimiter:
    def __init__(self, limits=None):
        self.limits = limits or DEFAULT_LIMITS.copy()
        self.counters = defaultdict(list)  # key -> [timestamps]

    def _prune(self, key, window=60):
        now = time()
        self.counters[key] = [t for t in self.counters[key] if now - t < window]

    def allow(self, key, limit):
        self._prune(key)
        if len(self.counters[key]) < limit:
            self.counters[key].append(time())
            return True
        return False

    def check(self, tenant_id, monolith, event_type):
        # Checa limites para cada domínio
        if not self.allow(f"tenant:{tenant_id}", self.limits["tenant"]):
            return False, "RATE_LIMIT_TENANT"
        if not self.allow(f"monolith:{monolith}", self.limits["monolith"]):
            return False, "RATE_LIMIT_MONOLITH"
        if not self.allow(f"event_type:{event_type}", self.limits["event_type"]):
            return False, "RATE_LIMIT_EVENT_TYPE"
        return True, None

# Instância global (pode ser singleton/externa)
rate_limiter = RateLimiter()

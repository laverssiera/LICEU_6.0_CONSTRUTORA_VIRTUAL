# Flag global de proteção de governança
GOVERNANCE_LOCKED = False  # Só o Monolito pode alterar

# Versionamento obrigatório para heurísticas do shadow_monolith
SHADOW_MONOLITH_HEURISTICS_VERSION = "1.0.0"

class GovernanceModificationError(Exception):
    pass

def require_monolith_approval():
    if GOVERNANCE_LOCKED:
        raise GovernanceModificationError("Alteração de governança bloqueada. Só o Monolito pode aprovar.")

# Exemplo de uso em autonomy_enforcement:
def update_autonomy_policy(new_policy, approved_by_monolith=False):
    if not approved_by_monolith:
        require_monolith_approval()
    # ...aplica política...
    return True

# Exemplo de uso em heurísticas do shadow_monolith:
def update_shadow_heuristics(new_heuristics, version, approved_by_monolith=False):
    if not approved_by_monolith:
        require_monolith_approval()
    global SHADOW_MONOLITH_HEURISTICS_VERSION
    SHADOW_MONOLITH_HEURISTICS_VERSION = version
    # ...aplica heurística...
    return True

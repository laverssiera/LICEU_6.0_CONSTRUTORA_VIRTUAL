"""
Feature flags globais para ativação incremental das novas camadas cognitivas/federadas.
Sempre fail-open e shadow por padrão.
"""

import os

def is_enabled(flag: str, default: bool = False) -> bool:
    """Verifica se uma feature flag está ativada via variável de ambiente."""
    val = os.getenv(flag)
    if val is None:
        return default
    return val.lower() in ("1", "true", "on", "yes")

# Exemplos de uso:
ENABLE_FEDERATION_RUNTIME = is_enabled("ENABLE_FEDERATION_RUNTIME")
ENABLE_WORLD_STATE = is_enabled("ENABLE_WORLD_STATE")
ENABLE_SEMANTIC_OBSERVABILITY = is_enabled("ENABLE_SEMANTIC_OBSERVABILITY")
ENABLE_CONSENSUS_RUNTIME = is_enabled("ENABLE_CONSENSUS_RUNTIME")
ENABLE_HOME_RUNTIME = is_enabled("ENABLE_HOME_RUNTIME")
ENABLE_META_PROJECT_RUNTIME = is_enabled("ENABLE_META_PROJECT_RUNTIME")
ENABLE_AI_FEDERATION = is_enabled("ENABLE_AI_FEDERATION")

# Exemplo de shadow mode:
def run_federation_runtime_shadow():
    if ENABLE_FEDERATION_RUNTIME:
        print("[Federation Runtime] Ativado!")
        # Inicializa federation control plane...
    else:
        print("[Federation Runtime] Shadow mode (apenas observação)")
        # Apenas coleta/observa, sem afetar produção

# Idem para as demais camadas...

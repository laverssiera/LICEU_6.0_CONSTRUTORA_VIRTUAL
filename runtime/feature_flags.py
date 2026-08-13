# Feature flag global para modo produção com dinheiro real
import os

REAL_MONEY_MODE = os.getenv("REAL_MONEY_MODE", "false").lower() == "true"

def is_real_money_mode():
    return REAL_MONEY_MODE

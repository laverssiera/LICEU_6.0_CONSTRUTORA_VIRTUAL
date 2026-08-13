# Auto-tuning de thresholds do circuit breaker
import sqlite3
from runtime.circuit_breaker import CircuitBreaker

DB_PATH = "event_store.db"

# Ajusta threshold com base na média histórica de DLQ

def compute_dlq_rate(window=1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT COUNT(*) FROM event_store WHERE type='dlq' ORDER BY timestamp DESC LIMIT ?", (window,))
    dlq = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM event_store ORDER BY timestamp DESC LIMIT ?", (window,))
    total = cur.fetchone()[0]
    conn.close()
    return dlq / total if total else 0.0

def auto_tune_circuit_breaker(cb: CircuitBreaker, window=1000):
    dlq_rate = compute_dlq_rate(window)
    # Exemplo: threshold = média histórica + 50%
    new_threshold = min(1.0, dlq_rate * 1.5)
    print(f"[AUTO-TUNING] Ajustando threshold do circuit breaker para {new_threshold:.3f}")
    cb.threshold = new_threshold

if __name__ == "__main__":
    cb = CircuitBreaker()
    auto_tune_circuit_breaker(cb)

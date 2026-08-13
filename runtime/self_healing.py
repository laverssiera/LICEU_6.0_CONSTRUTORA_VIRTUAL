# Self-healing automation: monitora saúde e reprocessa eventos
import time
from runtime.system_score import get_system_health
from runtime.circuit_breaker import CircuitBreaker

DLQ_PATH = "event_store.db"  # Supondo eventos DLQ também persistidos

def fetch_dlq_events():
    import sqlite3
    conn = sqlite3.connect(DLQ_PATH)
    cur = conn.execute("SELECT id, type, payload, pipeline_id, timestamp FROM event_store WHERE type='dlq' AND payload LIKE '%TRANSIENT%'")
    events = []
    for row in cur.fetchall():
        events.append({
            "id": row[0],
            "type": row[1],
            "payload": eval(row[2]),
            "pipeline_id": row[3],
            "timestamp": row[4],
        })
    conn.close()
    return events

breaker = CircuitBreaker(threshold=0.1, window=60)

def self_heal():
    health = get_system_health()
    print(f"[SELF-HEALING] System health: {health}")
    if health["system_health"] < 0.95:
        dlq_events = fetch_dlq_events()
        for event in dlq_events:
            print(f"[SELF-HEALING] Reprocessando evento DLQ: {event['id']}")
            # Aqui: lógica de retry real
            # Exemplo: publish_event(event['type'], event['payload'], ...)
    if health["dlq_rate"] > breaker.threshold:
        breaker.record_failure()
        if breaker.is_disabled():
            print("[SELF-HEALING] Circuit breaker acionado! Monólito desabilitado.")
    else:
        breaker.record_success()

if __name__ == "__main__":
    while True:
        self_heal()
        time.sleep(60)

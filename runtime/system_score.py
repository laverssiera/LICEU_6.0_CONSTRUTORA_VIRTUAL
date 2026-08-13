# Score de confiabilidade do sistema
import sqlite3

DB_PATH = "event_store.db"

# Exemplo de cálculo simples

def get_system_health():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT COUNT(*) FROM event_store")
    total_events = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM event_store WHERE type LIKE '%invalid%'")
    invalid_events = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM event_store WHERE type LIKE '%retry%'")
    retry_events = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM event_store WHERE type LIKE '%dlq%'")
    dlq_events = cur.fetchone()[0]
    conn.close()
    event_success_rate = (total_events - invalid_events - dlq_events) / total_events if total_events else 1.0
    dlq_rate = dlq_events / total_events if total_events else 0.0
    retry_rate = retry_events / total_events if total_events else 0.0
    system_health = event_success_rate * (1 - dlq_rate)
    return {
        "system_health": round(system_health, 3),
        "event_success_rate": round(event_success_rate, 3),
        "dlq_rate": round(dlq_rate, 3),
        "retry_rate": round(retry_rate, 3)
    }

if __name__ == "__main__":
    print(get_system_health())

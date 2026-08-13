# RCA automático: identifica causa raiz de falhas recorrentes
import sqlite3
from collections import Counter

DB_PATH = "event_store.db"

# Busca eventos DLQ e findings recentes

def fetch_recent_dlq_findings(limit=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT payload FROM event_store WHERE type IN ('dlq', 'audit.finding') ORDER BY timestamp DESC LIMIT ?", (limit,))
    reasons = []
    for row in cur.fetchall():
        payload = eval(row[0])
        reason = payload.get("reason") or payload.get("motivo")
        if reason:
            reasons.append(reason)
    conn.close()
    return reasons

def rca():
    reasons = fetch_recent_dlq_findings()
    if not reasons:
        print("Nenhuma falha recente para RCA.")
        return
    count = Counter(reasons)
    top = count.most_common(3)
    print("[RCA] Principais causas raiz de falha:")
    for reason, qty in top:
        print(f"- {reason}: {qty} ocorrências")

if __name__ == "__main__":
    rca()

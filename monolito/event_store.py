# Persistência de eventos (Event Store)
# Tabela: event_store (id, type, payload, timestamp, correlation_id)

import sqlite3
from datetime import datetime

DB_PATH = "event_store.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS event_store (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    correlation_id TEXT
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db()
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def persist_event(event, correlation_id=None):
    if "tenant_id" not in event or not event["tenant_id"]:
        raise ValueError("Evento sem tenant_id (obrigatório para isolamento multi-tenant)")
    conn = get_db()
    conn.execute(
        "INSERT INTO event_store (id, type, payload, tenant_id, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?)",
        (
            event.get("id"),
            event.get("type"),
            str(event.get("payload")),
            event.get("tenant_id"),
            event.get("timestamp", datetime.utcnow().isoformat()),
            correlation_id,
        ),
    )
    conn.commit()
    conn.close()

def replay_events(handler, tenant_id, from_timestamp=None, to_timestamp=None):
    conn = get_db()
    query = "SELECT id, type, payload, tenant_id, timestamp, correlation_id FROM event_store WHERE tenant_id=?"
    params = [tenant_id]
    if from_timestamp and to_timestamp:
        query += " AND timestamp BETWEEN ? AND ?"
        params += [from_timestamp, to_timestamp]
    elif from_timestamp:
        query += " AND timestamp >= ?"
        params += [from_timestamp]
    elif to_timestamp:
        query += " AND timestamp <= ?"
        params += [to_timestamp]
    for row in conn.execute(query, params):
        event = {
            "id": row[0],
            "type": row[1],
            "payload": eval(row[2]),
            "tenant_id": row[3],
            "timestamp": row[4],
            "correlation_id": row[5],
        }
        handler(event)
    conn.close()

if __name__ == "__main__":
    init_db()
    # Exemplo de persistência multi-tenant
    evento = {"id": "evt1", "type": "lead.created", "payload": {"foo": 1}, "tenant_id": "tenant-1", "timestamp": datetime.utcnow().isoformat()}
    persist_event(evento, correlation_id="corr-123")
    print("Evento persistido!")
    # Exemplo de replay
    def print_event(evt):
        print(f"Replay: {evt}")
    replay_events(print_event, "tenant-1")

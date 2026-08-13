# Replay determinístico de pipeline
import sqlite3
from kanban.pipeline_history import get_db as get_kanban_db

DB_PATH = "event_store.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS event_store (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    pipeline_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    cost REAL
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

def persist_event(event):
    if "tenant_id" not in event or not event["tenant_id"]:
        raise ValueError("Evento sem tenant_id (obrigatório para isolamento multi-tenant)")
    cost = event.get("cost")
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO event_store (id, type, payload, pipeline_id, tenant_id, timestamp, cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            event["id"],
            event["type"],
            str(event["payload"]),
            event["pipeline_id"],
            event["tenant_id"],
            event["timestamp"],
            cost,
        ),
    )
    conn.commit()
    conn.close()

def load_events(pipeline_id, tenant_id):
    conn = get_db()
    cur = conn.execute("SELECT id, type, payload, pipeline_id, tenant_id, timestamp, cost FROM event_store WHERE pipeline_id=? AND tenant_id=? ORDER BY timestamp ASC", (pipeline_id, tenant_id))
    events = []
    for row in cur.fetchall():
        events.append({
            "id": row[0],
            "type": row[1],
            "payload": eval(row[2]),
            "pipeline_id": row[3],
            "tenant_id": row[4],
            "timestamp": row[5],
            "cost": row[6],
        })
    conn.close()
    return events

def replay_pipeline(pipeline_id, tenant_id, apply_fn):
    events = load_events(pipeline_id, tenant_id)
    for event in events:
        apply_fn(event)

if __name__ == "__main__":
    init_db()
    # Exemplo: replay de pipeline multi-tenant
    def print_event(evt):
        print(f"Replay: {evt}")
    replay_pipeline("pipeline-1", "tenant-1", print_event)

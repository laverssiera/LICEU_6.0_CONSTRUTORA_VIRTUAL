# Controle de idempotência global (runtime)
import sqlite3
from datetime import datetime

DB_PATH = "event_idempotency.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS processed_events (
    event_id TEXT PRIMARY KEY,
    processed_at TEXT
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

def is_event_processed(event_id):
    conn = get_db()
    cur = conn.execute("SELECT 1 FROM processed_events WHERE event_id=?", (event_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def mark_event_processed(event_id):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO processed_events (event_id, processed_at) VALUES (?, ?)", (event_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(is_event_processed("evt-123"))
    mark_event_processed("evt-123")
    print(is_event_processed("evt-123"))

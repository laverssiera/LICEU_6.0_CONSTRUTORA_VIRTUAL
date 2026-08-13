# Snapshots de estado do pipeline
import sqlite3
from datetime import datetime

DB_PATH = "pipeline_snapshots.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_snapshots (
    pipeline_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    state TEXT NOT NULL,
    last_event_id TEXT NOT NULL,
    snapshot_at TEXT NOT NULL,
    PRIMARY KEY (pipeline_id, tenant_id)
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

def save_snapshot(pipeline_id, tenant_id, state, last_event_id):
    if not tenant_id:
        raise ValueError("tenant_id obrigatório para snapshot multi-tenant")
    conn = get_db()
    conn.execute(
        "REPLACE INTO pipeline_snapshots (pipeline_id, tenant_id, state, last_event_id, snapshot_at) VALUES (?, ?, ?, ?, ?)",
        (pipeline_id, tenant_id, str(state), last_event_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def load_snapshot(pipeline_id, tenant_id):
    conn = get_db()
    cur = conn.execute("SELECT state, last_event_id FROM pipeline_snapshots WHERE pipeline_id=? AND tenant_id=?", (pipeline_id, tenant_id))
    row = cur.fetchone()
    conn.close()
    if row:
        return eval(row[0]), row[1]
    return None, None

if __name__ == "__main__":
    init_db()
    save_snapshot("pipeline-1", "tenant-1", {"stage": "VIABILIDADE_FINANCEIRA"}, "evt-123")
    print(load_snapshot("pipeline-1", "tenant-1"))

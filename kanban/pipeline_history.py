# Auditoria de transição de pipeline
import sqlite3
from datetime import datetime

DB_PATH = "kanban.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    from_stage TEXT NOT NULL,
    to_stage TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    policy_version TEXT
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

def log_transition(pipeline_id, tenant_id, from_stage, to_stage, actor, policy_version=None):
    if not tenant_id:
        raise ValueError("tenant_id obrigatório para auditoria multi-tenant")
    conn = get_db()
    conn.execute(
        "INSERT INTO pipeline_history (pipeline_id, tenant_id, from_stage, to_stage, actor, timestamp, policy_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pipeline_id, tenant_id, from_stage, to_stage, actor, datetime.utcnow().isoformat(), policy_version),
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    log_transition("pipeline-1", "tenant-1", "IDEIA", "ESTUDO_TECNICO", "user-123", policy_version="v3.2")
    print("Transição auditada!")

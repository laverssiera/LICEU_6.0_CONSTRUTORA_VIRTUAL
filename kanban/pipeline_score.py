# Score do pipeline integrado ao CEA (brain_lib)
import sqlite3
from brain_lib.market import viability_score, decision
from datetime import datetime

DB_PATH = "kanban.db"

CREATE_SCORE_TABLE = """
CREATE TABLE IF NOT EXISTS pipeline_score (
    pipeline_id TEXT PRIMARY KEY,
    viability_score REAL,
    risk TEXT,
    roi REAL,
    calculated_at TEXT
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db()
    conn.execute(CREATE_SCORE_TABLE)
    conn.commit()
    conn.close()

def calculate_and_store_score(pipeline_id, demand, supply, risk_value, roi):
    score = viability_score(demand, supply, risk_value)
    risk_level = "high" if score < 40 else "medium" if score < 70 else "low"
    conn = get_db()
    conn.execute(
        "REPLACE INTO pipeline_score (pipeline_id, viability_score, risk, roi, calculated_at) VALUES (?, ?, ?, ?, ?)",
        (pipeline_id, score, risk_level, roi, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    print(f"Score do pipeline {pipeline_id}: {score}, risco: {risk_level}, roi: {roi}")

if __name__ == "__main__":
    init_db()
    calculate_and_store_score("pipeline-1", demand=100, supply=30, risk_value=20, roi=0.32)

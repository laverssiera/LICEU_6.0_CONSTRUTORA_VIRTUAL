# Dashboard mínimo do Kanban (CLI/JSON)
import sqlite3
from collections import Counter
import json

DB_PATH = "kanban.db"

def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT to_stage FROM pipeline_history ORDER BY timestamp DESC")
    stages = [row[0] for row in cur.fetchall()]
    count = Counter(stages)
    print(json.dumps(count, indent=2, ensure_ascii=False))
    conn.close()

if __name__ == "__main__":
    dashboard()

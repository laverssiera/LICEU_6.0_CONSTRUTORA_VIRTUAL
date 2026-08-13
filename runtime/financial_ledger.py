# Ledger financeiro imutável
# Tabela: financial_ledger (id, event_id, type, amount, from_account, to_account, timestamp)
# Regra: append only (nunca update, nunca delete)

import sqlite3
from datetime import datetime

DB_PATH = "financial_ledger.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS financial_ledger (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    from_account TEXT NOT NULL,
    to_account TEXT NOT NULL,
    timestamp TEXT NOT NULL
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

def append_ledger_entry(event_id, type_, amount, from_account, to_account, timestamp=None, entry_id=None):
    if not entry_id:
        entry_id = f"ledger-{event_id}-{datetime.utcnow().isoformat()}"
    conn = get_db()
    conn.execute(
        "INSERT INTO financial_ledger (id, event_id, type, amount, from_account, to_account, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            entry_id,
            event_id,
            type_,
            amount,
            from_account,
            to_account,
            timestamp or datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

def query_ledger(event_id=None):
    conn = get_db()
    if event_id:
        cur = conn.execute("SELECT * FROM financial_ledger WHERE event_id=? ORDER BY timestamp ASC", (event_id,))
    else:
        cur = conn.execute("SELECT * FROM financial_ledger ORDER BY timestamp ASC")
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    # Exemplo de uso
    append_ledger_entry(
        event_id="evt-123",
        type_="payment.generated",
        amount=1000.0,
        from_account="cliente-1",
        to_account="empresa-1"
    )
    print(query_ledger())

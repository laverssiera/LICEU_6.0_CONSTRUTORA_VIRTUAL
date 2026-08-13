# Integração com John: sugestão/priorização/alerta
import sqlite3

DB_PATH = "kanban.db"

# Exemplo: John sugere avanço para pipelines com maior score e alerta travamento

def sugerir_avanco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT pipeline_id, viability_score FROM pipeline_score ORDER BY viability_score DESC")
    for row in cur.fetchall():
        print(f"John sugere priorizar pipeline {row[0]} (score={row[1]})")
    conn.close()

def alertar_travamento():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT pipeline_id, to_stage, MAX(timestamp) FROM pipeline_history GROUP BY pipeline_id")
    for row in cur.fetchall():
        # Exemplo: alerta se pipeline parado em estágio intermediário
        if row[1] not in ("APROVADO", "REPROVADO", "COMPLETED"):
            print(f"John alerta: pipeline {row[0]} parado em {row[1]}")
    conn.close()

if __name__ == "__main__":
    sugerir_avanco()
    alertar_travamento()

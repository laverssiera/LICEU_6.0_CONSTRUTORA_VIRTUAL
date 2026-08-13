# Previsão de falhas simples baseada em tendência de DLQ
import sqlite3
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "event_store.db"

# Coleta contagem de DLQ por intervalo de tempo

def dlq_trend(hours=6, interval=1):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow()
    counts = []
    for i in range(hours, 0, -interval):
        start = now - timedelta(hours=i)
        end = now - timedelta(hours=i-interval)
        cur = conn.execute("SELECT COUNT(*) FROM event_store WHERE type='dlq' AND timestamp BETWEEN ? AND ?", (start.isoformat(), end.isoformat()))
        counts.append(cur.fetchone()[0])
    conn.close()
    return counts

def predict_failure():
    trend = dlq_trend()
    if len(trend) < 2:
        print("[PREDICT] Dados insuficientes para previsão.")
        return
    x = np.arange(len(trend))
    y = np.array(trend)
    coef = np.polyfit(x, y, 1)[0]
    print(f"[PREDICT] Tendência de DLQ: {trend}, coeficiente: {coef:.2f}")
    if coef > 0.5:
        print("[PREDICT] ALERTA: Risco de falha iminente detectado!")
    else:
        print("[PREDICT] Sistema estável.")

if __name__ == "__main__":
    predict_failure()

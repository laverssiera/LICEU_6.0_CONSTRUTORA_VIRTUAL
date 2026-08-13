"""
runtime_discovery.py
Descobre monólitos ativos, sincroniza registry, atualiza trust score, publica topology map.
"""

import requests

def discover_monoliths():
    r = requests.get("http://localhost:8080/runtime/status")
    if r.status_code == 200:
        data = r.json()
        print("[DISCOVERY] Monólitos online:")
        for m in data.get("monoliths_online", []):
            print(f"- {m['nome']} ({m['endpoint']}) trust: {m['federation_trust_score']}")
    else:
        print("[DISCOVERY] Falha ao obter monólitos.")

if __name__ == "__main__":
    discover_monoliths()

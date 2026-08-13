"""
runtime_healthcheck.py
Valida saúde do ecossistema federado LICEU 6.0
"""

import requests

def check(url, label):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            print(f"[OK] {label}")
        else:
            print(f"[FAIL] {label}")
    except Exception as e:
        print(f"[FAIL] {label}: {e}")

if __name__ == "__main__":
    check("http://localhost:8080/runtime/status", "Runtime Kernel")
    check("http://localhost:8080/runtime/topology", "Runtime Topology")
    check("http://localhost:8080/runtime/collective-mind", "Collective Mind")

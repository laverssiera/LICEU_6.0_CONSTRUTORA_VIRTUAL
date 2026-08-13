#!/usr/bin/env python3
"""
Valida se todos os eventos usados no código estão registrados em core_dna/event_names.json.
Falha (exit 1) se encontrar divergência.
"""
import os
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
EVENTS_PATH = ROOT / "core_dna" / "event_names.json"

# Carrega eventos válidos
with open(EVENTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
    valid_events = set((e["name"], e["version"]) for e in data["events"])

# Busca por eventos usados no código (ex: publish("lead.created", ..., version="v1"))
EVENT_PATTERN = re.compile(r'publish\s*\(\s*["\\\']([\w.]+)["\\\'].*?version\s*=\s*["\\\'](v\d+)["\\\']', re.DOTALL)

used_events = set()

for folder in [ROOT / "liceu-6.0" / "core-sdk", ROOT / "monolito", ROOT / "monolito_exemplo"]:
    for path in folder.rglob("*.py"):
        try:
            code = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in EVENT_PATTERN.finditer(code):
            used_events.add((match.group(1), match.group(2)))

# Verifica divergências
not_registered = used_events - valid_events
if not_registered:
    print("[ERRO] Eventos não registrados em core_dna/event_names.json:")
    for name, version in sorted(not_registered):
        print(f"  - {name} (version={version})")
    sys.exit(1)
else:
    print("[OK] Todos os eventos usados estão registrados.")
    sys.exit(0)

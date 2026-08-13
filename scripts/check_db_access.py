#!/usr/bin/env python3
"""
Script de enforcement: proíbe acesso direto ao banco entre módulos.
Busca por imports de drivers SQL/ORM fora de pastas permitidas.
"""
import os
import sys
from pathlib import Path
import re

ROOT = Path(__file__).parent.parent
ALLOWED = {"core_dna", "database", "event_store"}
PATTERN = re.compile(r"import (sqlite3|sqlalchemy|psycopg2|pymysql|mysql|aiomysql|asyncpg)")

violations = []
for path in ROOT.rglob("*.py"):
    if any(allowed in str(path) for allowed in ALLOWED):
        continue
    try:
        code = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for match in PATTERN.finditer(code):
        violations.append(f"{path}: {match.group(0)}")

if violations:
    print("[ERRO] Acesso direto ao banco encontrado:")
    for v in violations:
        print("  -", v)
    sys.exit(1)
else:
    print("[OK] Nenhum acesso direto ao banco fora dos módulos permitidos.")

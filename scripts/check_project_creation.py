# Enforcement: proibir criação direta de projeto fora do Kanban
import sys
from pathlib import Path
import re

ROOT = Path(__file__).parent.parent
PATTERN = re.compile(r"project\.created|create_project|insert into project", re.IGNORECASE)

violations = []
for path in ROOT.rglob("*.py"):
    if "kanban" in str(path):
        continue  # Só Kanban pode criar projeto
    try:
        code = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for match in PATTERN.finditer(code):
        violations.append(f"{path}: {match.group(0)}")

if violations:
    print("[ERRO] Criação direta de projeto fora do Kanban encontrada:")
    for v in violations:
        print("  -", v)
    sys.exit(1)
else:
    print("[OK] Nenhuma criação direta de projeto fora do Kanban.")

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v alembic >/dev/null 2>&1; then
	ALEMBIC_BIN="$(command -v alembic)"
else
	ALEMBIC_BIN="$(python - <<'PY'
import sysconfig
print(sysconfig.get_path('scripts') + '/alembic')
PY
)"
fi

if [[ ! -x "$ALEMBIC_BIN" ]]; then
	echo "[bootstrap] Alembic nao encontrado. Instale com: python -m pip install alembic"
	exit 1
fi

echo "[bootstrap] Running Alembic migrations..."
"$ALEMBIC_BIN" -c alembic.ini upgrade head

echo "[bootstrap] Running legacy RBAC seed..."
python scripts/seed_rbac.py

echo "[bootstrap] Running enterprise bootstrap seed..."
python scripts/seed_enterprise_bootstrap.py

echo "[bootstrap] Completed successfully."

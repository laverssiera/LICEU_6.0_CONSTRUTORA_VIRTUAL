#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

DRY_RUN=0
STRICT_PREFLIGHT=0
PREFLIGHT_ERRORS=0

usage() {
  cat <<'EOF'
Usage: ./scripts/staging_enterprise_rollout.sh [--dry-run] [--strict-preflight]

Options:
  --dry-run           Print and validate rollout plan without applying DB changes.
  --strict-preflight  Fail if any preflight check is missing/invalid.
  -h, --help          Show this help message.
EOF
}

preflight_warn_or_fail() {
  local message="$1"
  if [[ "$STRICT_PREFLIGHT" -eq 1 ]]; then
    echo "[rollout] ERROR: ${message}"
    PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
  elif [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[rollout][dry-run] WARNING: ${message}"
  else
    echo "[rollout] ${message}"
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --strict-preflight)
      STRICT_PREFLIGHT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[rollout] Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${DATABASE_URL:-}" ]]; then
  preflight_warn_or_fail "DATABASE_URL is not set."
fi

if [[ -n "${DATABASE_URL:-}" && "${DATABASE_URL}" != postgresql* ]]; then
  preflight_warn_or_fail "DATABASE_URL is not PostgreSQL. Current: ${DATABASE_URL}"
fi

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
  preflight_warn_or_fail "Alembic not found. Install with: python -m pip install alembic"
fi

if ! command -v psql >/dev/null 2>&1; then
  preflight_warn_or_fail "psql not found. Install PostgreSQL client to run sanity checks."
fi

if [[ "$PREFLIGHT_ERRORS" -gt 0 ]]; then
  echo "[rollout] Preflight failed with ${PREFLIGHT_ERRORS} error(s)."
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[rollout][dry-run] Plan:"
  echo "[rollout][dry-run] 1) $ALEMBIC_BIN -c alembic.ini upgrade head"
  echo "[rollout][dry-run] 2) python scripts/seed_rbac.py"
  echo "[rollout][dry-run] 3) python scripts/seed_enterprise_bootstrap.py"
  echo "[rollout][dry-run] 4) psql \"\$DATABASE_URL\" -v ON_ERROR_STOP=1 -f scripts/post_migration_sanity.sql"
  echo "[rollout][dry-run] Completed (no changes applied)."
  exit 0
fi

echo "[rollout] Running migrations to head..."
"$ALEMBIC_BIN" -c alembic.ini upgrade head

echo "[rollout] Running seeds..."
python scripts/seed_rbac.py
python scripts/seed_enterprise_bootstrap.py

echo "[rollout] Running SQL sanity checks..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/post_migration_sanity.sql

echo "[rollout] Enterprise staging rollout completed successfully."

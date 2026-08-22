#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_output="$($ROOT_DIR/scripts/check_disk_capacity.sh /workspaces || true)"
echo "$check_output"

status=$(echo "$check_output" | python -c 'import sys,json; print(json.load(sys.stdin).get("status","UNKNOWN"))')

if [[ "$status" == "CRITICAL" ]]; then
  echo "[BLOCKED] Disk capacity is CRITICAL. Build aborted to prevent ENOSPC." >&2
  exit 2
fi

if [[ "$status" == "WARNING" ]]; then
  echo "[WARN] Disk capacity is WARNING. Proceeding with build." >&2
fi

cd "$ROOT_DIR"
docker compose build backend
docker compose up -d backend
docker compose ps backend

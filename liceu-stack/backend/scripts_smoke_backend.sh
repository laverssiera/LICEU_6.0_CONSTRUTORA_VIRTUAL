#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8010}"

echo "[smoke] Health check"
HEALTH=$(curl -sS "${API_BASE}/health")
echo "${HEALTH}"

echo "[smoke] Criando negocio"
CREATE_PAYLOAD='{
  "title": "Empreendimento 20 casas",
  "portfolio": "Obras Comuns",
  "program": "Residencial",
  "stage": "Ideia",
  "estimated_cost": 2000000,
  "expected_return": 3200000
}'

CREATED=$(curl -sS -X POST "${API_BASE}/business/" \
  -H "Content-Type: application/json" \
  -d "${CREATE_PAYLOAD}")

echo "${CREATED}"

BUSINESS_ID=$(python - <<'PY' "${CREATED}"
import json
import sys
payload = json.loads(sys.argv[1])
print(payload.get("id", ""))
PY
)

if [[ -z "${BUSINESS_ID}" ]]; then
  echo "[smoke] Falha ao obter id do negocio"
  exit 1
fi

echo "[smoke] Aprovando negocio ${BUSINESS_ID}"
APPROVED=$(curl -sS -X POST "${API_BASE}/business/${BUSINESS_ID}/approve")
echo "${APPROVED}"

echo "[smoke] OK"

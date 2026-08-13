#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
USER_NAME="${USER_NAME:-irmandade_demo}"
USER_PASS="${USER_PASS:-demo123}"
PORTAL="${PORTAL:-workspace}"

if ! command -v curl >/dev/null 2>&1; then
  echo "[demo] curl not found"
  exit 1
fi

LOGIN_PAYLOAD=$(cat <<JSON
{"username":"${USER_NAME}","password":"${USER_PASS}","portal":"${PORTAL}"}
JSON
)

TOKEN_RESPONSE=$(curl -sS -X POST "${API_BASE}/auth/sso/login" \
  -H "Content-Type: application/json" \
  -d "${LOGIN_PAYLOAD}")

ACCESS_TOKEN=$(python - <<'PY' "${TOKEN_RESPONSE}"
import json, sys
payload = json.loads(sys.argv[1])
print(payload.get("access_token", ""))
PY
)

if [[ -z "${ACCESS_TOKEN}" ]]; then
  echo "[demo] login failed"
  echo "${TOKEN_RESPONSE}"
  exit 1
fi

DEMO_PAYLOAD='{
  "title": "Empreendimento 20 casas",
  "portfolio": "Obras Comuns",
  "program": "Residencial",
  "estimated_cost": 2000000,
  "expected_return": 3200000,
  "simulate_error": true,
  "close_duration": 18,
  "timeline_hours": 24,
  "timeline_limit": 200
}'

RESULT=$(curl -sS -X POST "${API_BASE}/business-pipeline/demo/first-flow" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "${DEMO_PAYLOAD}")

python - <<'PY' "${RESULT}"
import json, sys
payload = json.loads(sys.argv[1])
if payload.get("status") != "completed":
    print("[demo] flow failed")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)

timeline = payload.get("timeline", {})
steps = timeline.get("steps", [])
done = [s.get("name") for s in steps if s.get("done")]
print("[demo] status=completed")
print(f"[demo] pipeline_id={payload.get('pipeline_id')}")
print(f"[demo] project_id={payload.get('project_id')}")
print(f"[demo] events_returned={len(timeline.get('events', []))}")
print("[demo] completed_steps=" + ", ".join(done))
PY

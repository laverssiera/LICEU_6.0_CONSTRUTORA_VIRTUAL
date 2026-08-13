#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/home/codespace/.python/current/bin/python}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-18080}"
API_BASE="http://${API_HOST}:${API_PORT}"
TARGET_PORT="${TARGET_PORT:-8000}"

log() {
  echo "[planet-preflight] $*"
}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  log "python binario nao encontrado/executavel: ${PYTHON_BIN}"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  log "curl nao encontrado"
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  if lsof -i ":${TARGET_PORT}" >/dev/null 2>&1; then
    log "aviso: porta alvo ${TARGET_PORT} esta ocupada (pode impactar execucao manual do kernel)"
  else
    log "ok: porta alvo ${TARGET_PORT} livre"
  fi
fi

log "executando testes do Planet Runtime"
cd "${ROOT_DIR}"
"${PYTHON_BIN}" -m pytest -q tests/test_planet_runtime.py tests/test_planet_runtime_api.py

log "subindo kernel temporario para smoke test HTTP em ${API_BASE}"
"${PYTHON_BIN}" -m uvicorn runtime.kernel_app:app --host "${API_HOST}" --port "${API_PORT}" >/tmp/planet_runtime_preflight_uvicorn.log 2>&1 &
UVICORN_PID=$!

cleanup() {
  if [[ -n "${UVICORN_PID:-}" ]] && kill -0 "${UVICORN_PID}" >/dev/null 2>&1; then
    kill "${UVICORN_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

log "aguardando endpoint OpenAPI responder"
"${PYTHON_BIN}" - <<'PY' "${API_BASE}"
import sys
import time
from urllib import request

base = sys.argv[1]
url = f"{base}/openapi.json"
last_error = None
for _ in range(40):
    try:
        with request.urlopen(url, timeout=0.5) as resp:
            if resp.status == 200:
                raise SystemExit(0)
    except Exception as exc:
        last_error = exc
    time.sleep(0.1)

print(f"openapi indisponivel: {last_error}")
raise SystemExit(1)
PY

log "validando endpoint /planetary/runtime/run"
HTTP_CODE=$(curl -sS -o /tmp/planet_runtime_preflight_response.json -w "%{http_code}" \
  -X POST "${API_BASE}/planetary/runtime/run" \
  -H "Content-Type: application/json" \
  -d '{"cycles":1,"cycle_interval_seconds":1}')

if [[ "${HTTP_CODE}" != "200" ]]; then
  log "falha no endpoint planetario: HTTP ${HTTP_CODE}"
  cat /tmp/planet_runtime_preflight_response.json
  exit 1
fi

"${PYTHON_BIN}" - <<'PY' /tmp/planet_runtime_preflight_response.json
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)

if payload.get("status") != "completed":
    print("status inesperado:", payload)
    raise SystemExit(1)

if payload.get("total_cycles") != 1:
    print("total_cycles inesperado:", payload)
    raise SystemExit(1)

ops = payload.get("operations", [])
if len(ops) != 1:
    print("operations inesperado:", payload)
    raise SystemExit(1)

print("planet runtime endpoint validado com sucesso")
PY

log "preflight concluido com sucesso"

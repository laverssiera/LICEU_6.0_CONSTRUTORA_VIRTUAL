#!/bin/bash
# Script de validação automática dos endpoints soberanos do LICEU CORE

set -e

BASE_URL="http://localhost:8000"
ENDPOINTS=(
  "/runtime/observability"
  "/runtime/agi-metrics"
  "/runtime/atlas-status"
  "/runtime/certification-status"
)

ALL_OK=1

for endpoint in "${ENDPOINTS[@]}"; do
  echo -n "Validando $endpoint ... "
  RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/resp.json "$BASE_URL$endpoint")
  HTTP_CODE=$(tail -c 3 <<< "$RESPONSE")
  cat /tmp/resp.json | jq . > /dev/null 2>&1 && JQ_OK=1 || JQ_OK=0
  if [[ "$HTTP_CODE" == "200" && $JQ_OK -eq 1 ]]; then
    echo "OK"
  else
    echo "FALHOU (HTTP $HTTP_CODE, JSON válido: $JQ_OK)"
    echo "Resposta bruta:"
    cat /tmp/resp.json
    ALL_OK=0
  fi
done

if [[ $ALL_OK -eq 1 ]]; then
  echo "\nTodos os endpoints estão operacionais e retornam JSON válido."
  exit 0
else
  echo "\nAlgum endpoint falhou. Veja acima para detalhes."
  exit 1
fi

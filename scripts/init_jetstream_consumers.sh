#!/bin/bash
# Cria consumers duráveis para cada monolito no JetStream

set -e

NATS_CLI=${NATS_CLI:-nats}
NATS_URL=${NATS_URL:-nats://localhost:4222}

# Lista de monolitos
MONOLITOS=(opera hub juridicotech archimedes backend)

for MONO in "${MONOLITOS[@]}"; do
  $NATS_CLI --server $NATS_URL consumer add LICEU_EVENTS "${MONO}_consumer" \
    --filter-subject "liceu.events.*" \
    --deliver-group "$MONO" \
    --ack explicit \
    --replay instant \
    --max-deliver 10 \
    --backoff "1s,5s,30s,2m,10m" \
    --description "Consumer durável para $MONO"
done

echo "Consumers duráveis criados/configurados para todos os monolitos."

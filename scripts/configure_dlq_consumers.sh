#!/bin/bash
# Configura DLQ automática para todos os consumers dos monolitos

set -e

NATS_CLI=${NATS_CLI:-nats}
NATS_URL=${NATS_URL:-nats://localhost:4222}

MONOLITOS=(opera hub juridicotech archimedes backend)

for MONO in "${MONOLITOS[@]}"; do
  $NATS_CLI --server $NATS_URL consumer update LICEU_EVENTS "${MONO}_consumer" \
    --max-deliver 10 \
    --deliver-group "$MONO" \
    --ack explicit \
    --replay instant \
    --backoff "1s,5s,30s,2m,10m" \
    --dlq-subject "liceu.dlq.${MONO}" \
    --description "Consumer com DLQ para $MONO"
done

echo "DLQ automática configurada para todos os consumers."

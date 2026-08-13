#!/bin/bash
# Inicializa os streams JetStream obrigatórios para o ecossistema LICEU 6.0

set -e

NATS_CLI=${NATS_CLI:-nats}
NATS_URL=${NATS_URL:-nats://localhost:4222}

# LICEU_EVENTS
$NATS_CLI --server $NATS_URL stream add LICEU_EVENTS \
  --subjects "liceu.events.*" \
  --storage file \
  --retention limits \
  --max-age 168h \
  --max-bytes 10737418240 \
  --max-msgs 1000000 \
  --description "Eventos principais do ecossistema"

# LICEU_AUDIT
$NATS_CLI --server $NATS_URL stream add LICEU_AUDIT \
  --subjects "liceu.audit.*" \
  --storage file \
  --retention limits \
  --max-age 720h \
  --max-bytes 21474836480 \
  --max-msgs 2000000 \
  --description "Eventos de auditoria e compliance"

# LICEU_DLQ
$NATS_CLI --server $NATS_URL stream add LICEU_DLQ \
  --subjects "liceu.dlq.*" \
  --storage file \
  --retention limits \
  --max-age 720h \
  --max-bytes 5368709120 \
  --max-msgs 500000 \
  --description "Dead Letter Queue para eventos rejeitados"

echo "Streams JetStream criados/configurados com sucesso."

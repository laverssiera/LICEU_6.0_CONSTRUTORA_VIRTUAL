#!/bin/bash
# start_collective_agi.sh
# Bootstrap completo do LICEU 6.0 Collective AGI Operating System

set -e

# Validar Docker
if ! command -v docker &> /dev/null; then
  echo "[ERROR] Docker não encontrado. Instale o Docker."
  exit 1
fi

echo "[INFO] Validando e subindo infraestrutura federada..."

docker compose -f ../docker-compose.runtime.yml up -d

# Validar NATS
if ! docker ps | grep -q nats; then
  echo "[ERROR] NATS não está rodando."
  exit 1
fi
# Validar Redis
if ! docker ps | grep -q redis; then
  echo "[ERROR] Redis não está rodando."
  exit 1
fi
# Validar Neo4j
if ! docker ps | grep -q neo4j; then
  echo "[ERROR] Neo4j não está rodando."
  exit 1
fi
# Validar PostgreSQL
if ! docker ps | grep -q postgres; then
  echo "[ERROR] PostgreSQL não está rodando."
  exit 1
fi

echo "[INFO] Iniciando observabilidade..."
./start_observability_stack.sh

echo "[INFO] Iniciando kernel principal..."
cd ../
python3 -m runtime.global_runtime_kernel &
KERNEL_PID=$!

sleep 5

echo "[INFO] Iniciando workers, federation mesh e agentes cognitivos..."
# Exemplos de inicialização (ajuste conforme evolução dos workers/agents)
python3 -m runtime.federation.runtime_federation_manager &
python3 -m runtime.cognition.runtime_orchestrator &
python3 -m runtime.agents.strategist_agent &
python3 -m runtime.agents.operations_agent &

wait $KERNEL_PID

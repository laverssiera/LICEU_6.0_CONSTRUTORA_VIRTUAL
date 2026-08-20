#!/bin/bash
# CANONICAL_DATABASE_CONNECTIVITY Diagnosis & Remediation
# Verifica e corrige conectividade entre monólitos e Canonical Event Store

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
VALIDATION_SCRIPT="${SCRIPT_DIR}/validate_canonical_connectivity.py"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações esperadas
EXPECTED_DB_HOST="db_core_os"
EXPECTED_DB_PORT="5432"
EXPECTED_DB_NAME="liceu_core_os"
EXPECTED_DB_USER="admin"
EXPECTED_NETWORK="liceu-net"

echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CANONICAL_DATABASE_CONNECTIVITY - DIAGNOSTIC & REMEDIATION${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"

# ============================================================================
# ETAPA 1: Verificar docker-compose.yml
# ============================================================================
echo -e "\n${YELLOW}[ETAPA 1/5] Verificando docker-compose.yml...${NC}"

if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo -e "${RED}✗ docker-compose.yml não encontrado em $DOCKER_COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose.yml encontrado${NC}"

# ============================================================================
# ETAPA 2: Verificar se db_core_os está definido
# ============================================================================
echo -e "\n${YELLOW}[ETAPA 2/5] Verificando se db_core_os está definido no docker-compose...${NC}"

if grep -q "db_core_os:" "$DOCKER_COMPOSE_FILE"; then
    echo -e "${GREEN}✓ Serviço db_core_os encontrado${NC}"
    
    # Extrair container_name
    if grep -A 5 "db_core_os:" "$DOCKER_COMPOSE_FILE" | grep -q "container_name: db_core_os"; then
        echo -e "${GREEN}  ✓ container_name: db_core_os${NC}"
    fi
    
    # Extrair configurações do banco
    if grep -A 10 "db_core_os:" "$DOCKER_COMPOSE_FILE" | grep -q "POSTGRES_DB: liceu_core_os"; then
        echo -e "${GREEN}  ✓ POSTGRES_DB: liceu_core_os${NC}"
    fi
    
    if grep -A 10 "db_core_os:" "$DOCKER_COMPOSE_FILE" | grep -q "POSTGRES_USER: admin"; then
        echo -e "${GREEN}  ✓ POSTGRES_USER: admin${NC}"
    fi
else
    echo -e "${RED}✗ Serviço db_core_os NÃO encontrado no docker-compose.yml${NC}"
    exit 1
fi

# ============================================================================
# ETAPA 3: Verificar rede liceu-net
# ============================================================================
echo -e "\n${YELLOW}[ETAPA 3/5] Verificando configuração da rede liceu-net...${NC}"

if grep -q "liceu-net:" "$DOCKER_COMPOSE_FILE"; then
    echo -e "${GREEN}✓ Rede liceu-net definida no docker-compose${NC}"
    
    if grep -A 5 "liceu-net:" "$DOCKER_COMPOSE_FILE" | grep -q "driver: bridge"; then
        echo -e "${GREEN}  ✓ Driver: bridge${NC}"
    fi
else
    echo -e "${RED}✗ Rede liceu-net NÃO está definida${NC}"
    exit 1
fi

# ============================================================================
# ETAPA 4: Verificar dependências e healthchecks
# ============================================================================
echo -e "\n${YELLOW}[ETAPA 4/5] Verificando dependências de db_core_os...${NC}"

# Verificar se há serviços que dependem de db_core_os
DEPENDENT_SERVICES=$(grep -B 3 "db_core_os:" "$DOCKER_COMPOSE_FILE" | grep "condition: service_healthy" | wc -l)

if [[ $DEPENDENT_SERVICES -gt 0 ]]; then
    echo -e "${GREEN}✓ Há $DEPENDENT_SERVICES serviço(s) dependendo de db_core_os${NC}"
else
    echo -e "${YELLOW}⚠ Nenhum serviço explicitamente depende de db_core_os${NC}"
    echo -e "${YELLOW}  (Isso pode ser OK se os consumidores resolvem DNS dinamicamente)${NC}"
fi

# ============================================================================
# ETAPA 5: Executar validação de conectividade
# ============================================================================
echo -e "\n${YELLOW}[ETAPA 5/5] Executando validação de conectividade...${NC}"

if [[ ! -f "$VALIDATION_SCRIPT" ]]; then
    echo -e "${RED}✗ Script de validação não encontrado: $VALIDATION_SCRIPT${NC}"
    exit 1
fi

# Exportar variáveis de ambiente para o script Python
export DB_HOST="$EXPECTED_DB_HOST"
export DB_PORT="$EXPECTED_DB_PORT"
export DB_NAME="$EXPECTED_DB_NAME"
export DB_USER="$EXPECTED_DB_USER"
export DB_PASSWORD="password123"

# Executar validação
if python3 "$VALIDATION_SCRIPT"; then
    VALIDATION_RESULT="PASS"
else
    VALIDATION_RESULT="FAILED"
fi

# ============================================================================
# RELATÓRIO FINAL
# ============================================================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}RELATÓRIO FINAL${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"

if [[ "$VALIDATION_RESULT" == "PASS" ]]; then
    echo -e "${GREEN}✅ CANONICAL_DATABASE_CONNECTIVITY VALIDADO COM SUCESSO${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "Status: PASS"
    echo -e "Todos os monólitos podem acessar db_core_os:"
    echo -e "  • CEA INVESTIMENTOS (cea_investimentos)"
    echo -e "  • ECONOTECH (econo_tech)"
    echo -e "  • FORNECEDORES (erp_fornecedores)"
    echo -e "  • BIM ARCH ENG (bim_arqu_eng)"
    echo -e "  • ARCHIMEDES (archimedes)"
    echo -e "  • OPERA (hub_contabil)"
    echo -e "  • CEFEIDA (cefeida)"
    echo -e "  • E demais consumidores do backbone canônico"
else
    echo -e "${RED}❌ FALHA NA CONECTIVIDADE CANÔNICA${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "Por favor, verifique o arquivo CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json"
    echo -e "para detalhes específicos do problema."
fi

echo -e "\n${YELLOW}Para mais detalhes, consulte:${NC}"
echo -e "  • CANONICAL_FEDERATION_BACKBONE_REPORT.md"
echo -e "  • CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json"
echo -e "  • docker logs db_core_os"

exit 0

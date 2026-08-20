#!/bin/bash
# CANONICAL_DATABASE_CONNECTIVITY - Quick Start & Test Guide
# Execute este script para começar a usar os validadores

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   CANONICAL_DATABASE_CONNECTIVITY - QUICK START GUIDE           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# ============================================================================
# VERIFICAR PRÉ-REQUISITOS
# ============================================================================
echo ""
echo "📋 [ETAPA 1/3] Verificando pré-requisitos..."
echo ""

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale com: apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 3 encontrado: $PYTHON_VERSION"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instale com: apt install python3-pip"
    exit 1
fi

echo "✓ pip3 encontrado"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    echo "  - Se executando em container Dev: Docker deve estar disponível"
    echo "  - Se executando em host: Instale Docker"
    exit 1
fi

DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,$//')
echo "✓ Docker encontrado: $DOCKER_VERSION"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠ docker-compose não encontrado. Tentando com 'docker compose'..."
    if ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose não encontrado."
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "✓ Docker Compose encontrado"

# ============================================================================
# INSTALAR DEPENDÊNCIAS PYTHON
# ============================================================================
echo ""
echo "📦 [ETAPA 2/3] Instalando dependências Python..."
echo ""

REQUIRED_PACKAGES=(
    "psycopg2-binary"
    "PyYAML"
)

INSTALL_NEEDED=false

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import ${package,,}" 2>/dev/null; then
        echo "✓ $package já instalado"
    else
        echo "⚠ $package não encontrado. Instalando..."
        INSTALL_NEEDED=true
    fi
done

if $INSTALL_NEEDED; then
    echo ""
    echo "Executando: pip3 install psycopg2-binary PyYAML"
    pip3 install psycopg2-binary PyYAML
    echo "✓ Dependências instaladas"
fi

# ============================================================================
# VERIFICAR ARQUIVOS
# ============================================================================
echo ""
echo "📄 [ETAPA 3/3] Verificando arquivos de validação..."
echo ""

REQUIRED_FILES=(
    "validate_canonical_connectivity.py"
    "validate_canonical_connectivity.sh"
    "remediate_canonical_connectivity.py"
    "docker-compose.yml"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✓ $file"
    else
        echo "❌ $file não encontrado"
        ALL_EXIST=false
    fi
done

if ! $ALL_EXIST; then
    echo ""
    echo "❌ Alguns arquivos estão faltando!"
    exit 1
fi

# ============================================================================
# MENU PRINCIPAL
# ============================================================================
echo ""
echo "═════════════════════════════════════════════════════════════════"
echo "✅ Pré-requisitos OK! Escolha uma opção:"
echo "═════════════════════════════════════════════════════════════════"
echo ""
echo "1️⃣  VALIDAR CONECTIVIDADE (recomendado para começar)"
echo "    bash validate_canonical_connectivity.sh"
echo ""
echo "2️⃣  REMEDIAR AUTOMATICAMENTE (se validação falhar)"
echo "    python3 remediate_canonical_connectivity.py"
echo ""
echo "3️⃣  TESTAR MANUALMENTE (diagnóstico customizado)"
echo "    Opções:"
echo "      • docker ps | grep db_core_os"
echo "      • docker logs db_core_os"
echo "      • docker network inspect liceu-net"
echo ""
echo "4️⃣  VER DOCUMENTAÇÃO"
echo "    • CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md (técnico)"
echo "    • README_CANONICAL_CONNECTIVITY.md (operacional)"
echo "    • CANONICAL_CONNECTIVITY_EXECUTIVE_SUMMARY.md (executivo)"
echo ""
echo "0️⃣  SAIR"
echo ""
echo "───────────────────────────────────────────────────────────────"

read -p "Escolha (0-4): " choice

case "$choice" in
    1)
        echo ""
        echo "▶ Executando: bash validate_canonical_connectivity.sh"
        echo ""
        bash validate_canonical_connectivity.sh
        echo ""
        echo "📊 Resultado disponível em: CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json"
        ;;
    2)
        echo ""
        echo "▶ Executando: python3 remediate_canonical_connectivity.py"
        echo ""
        python3 remediate_canonical_connectivity.py
        echo ""
        echo "✅ Remediação completa. Executar validação novamente:"
        echo "   bash validate_canonical_connectivity.sh"
        ;;
    3)
        echo ""
        echo "🔧 Testes Manuais Disponíveis:"
        echo ""
        echo "  1. Status do db_core_os:"
        echo "     docker ps | grep db_core_os"
        echo ""
        echo "  2. Logs do PostgreSQL:"
        echo "     docker logs db_core_os | tail -20"
        echo ""
        echo "  3. Verificar rede Docker:"
        echo "     docker network inspect liceu-net"
        echo ""
        echo "  4. Testar DNS (dentro de container):"
        echo "     docker exec <container> getent hosts db_core_os"
        echo ""
        echo "  5. Testar TCP (dentro de container):"
        echo "     docker exec <container> nc -zv db_core_os 5432"
        echo ""
        echo "  6. Testar PostgreSQL (dentro de container):"
        echo "     docker exec <container> psql -h db_core_os -U admin -d liceu_core_os -c 'SELECT 1'"
        echo ""
        ;;
    4)
        echo ""
        echo "📚 Documentação Disponível:"
        echo ""
        echo "  1. Guia Técnico (12 etapas mapeadas)"
        echo "     less CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md"
        echo ""
        echo "  2. Guia Operacional"
        echo "     less README_CANONICAL_CONNECTIVITY.md"
        echo ""
        echo "  3. Resumo Executivo"
        echo "     less CANONICAL_CONNECTIVITY_EXECUTIVE_SUMMARY.md"
        echo ""
        echo "Para abrir um arquivo:"
        echo "  • less <arquivo.md>"
        echo "  • cat <arquivo.md>"
        echo "  • nano <arquivo.md>"
        echo ""
        ;;
    0)
        echo "👋 Até logo!"
        exit 0
        ;;
    *)
        echo "❌ Opção inválida!"
        exit 1
        ;;
esac

echo ""
echo "═════════════════════════════════════════════════════════════════"
echo "✨ Operação concluída!"
echo "═════════════════════════════════════════════════════════════════"

#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-laverssiera/LICEU_6.0_CONSTRUTORA_VIRTUAL}"
MILESTONE="${MILESTONE:-Planejamento Estrategico}"
ASSIGNEES_CSV="${ASSIGNEES:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Erro: GitHub CLI (gh) nao encontrado no PATH." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Erro: voce nao esta autenticado no gh. Rode: gh auth login" >&2
  exit 1
fi

IFS=',' read -r -a ASSIGNEES <<<"$ASSIGNEES_CSV"

ensure_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$desc" \
    --force >/dev/null
}

ensure_milestone() {
  local number
  number="$(gh api "repos/$REPO/milestones" --paginate --jq ".[] | select(.title == \"$MILESTONE\") | .number" | head -n 1 || true)"

  if [[ -z "${number:-}" ]]; then
    gh api "repos/$REPO/milestones" -X POST -f "title=$MILESTONE" >/dev/null
    echo "Milestone criada: $MILESTONE"
  else
    echo "Milestone existente: $MILESTONE (#$number)"
  fi
}

create_issue() {
  local title="$1"
  local labels_csv="$2"
  local body="$3"

  local -a cmd
  local -a labels

  cmd=(gh issue create --repo "$REPO" --title "$title" --body "$body" --milestone "$MILESTONE")

  IFS=',' read -r -a labels <<<"$labels_csv"
  for label in "${labels[@]}"; do
    [[ -n "$label" ]] && cmd+=(--label "$label")
  done

  for assignee in "${ASSIGNEES[@]}"; do
    assignee="${assignee// /}"
    [[ -n "$assignee" ]] && cmd+=(--assignee "$assignee")
  done

  "${cmd[@]}"
}

# Labels principais
ensure_label "modulo:planejamento-estrategico" "0E8A16" "Modulo Planejamento Estrategico"
ensure_label "epic:core" "1D76DB" "Epic 1 - Core do modulo"
ensure_label "epic:integracao" "5319E7" "Epic 2 - Integracao com monolitos"
ensure_label "epic:execucao" "FBCA04" "Epic 3 - Motor de execucao"
ensure_label "epic:kanban" "D93F0B" "Epic 4 - Kanban estrategico"
ensure_label "epic:frontend" "0052CC" "Epic 5 - Frontend"
ensure_label "epic:governanca" "B60205" "Epic 6 - Governanca e seguranca"
ensure_label "epic:inteligencia" "C2E0C6" "Epic 7 - Inteligencia"
ensure_label "backend" "A2EEEF" "Trabalho backend"
ensure_label "frontend" "F9D0C4" "Trabalho frontend"
ensure_label "database" "C5DEF5" "Banco de dados"
ensure_label "api" "BFDADC" "API"
ensure_label "integration" "E4E669" "Integracao entre modulos"
ensure_label "security" "D4C5F9" "Seguranca"
ensure_label "ai" "006B75" "Inteligencia e recomendacao"

ensure_milestone

ISSUE_001_BODY=$(cat <<'EOF'
Implementar base de estrategias macro do modulo de planejamento.

## Checklist
- Criar tabela `strategies`
- Campos: `id`, `name`, `description`, `priority`, `status`
- Criar modelo ORM e schemas
- Criar CRUD FastAPI
- Criar testes basicos de CRUD
EOF
)

ISSUE_002_BODY=$(cat <<'EOF'
Criar entidade de objetivos (OKR) vinculada a estrategia.

## Checklist
- Criar tabela `objectives`
- Relacao `objective -> strategy`
- Campos: `metric`, `target`, `deadline`
- CRUD FastAPI e validacoes
- Testes basicos de relacionamento

## Dependencia
- Depende da Issue #001
EOF
)

ISSUE_003_BODY=$(cat <<'EOF'
Criar entidade de iniciativas estrategicas.

## Checklist
- Criar tabela `initiatives`
- Tipos permitidos: `process`, `training`, `execution`, `financial`
- Campo `owner` obrigatorio
- CRUD FastAPI com validacao de tipo
- Testes basicos

## Dependencia
- Depende da Issue #002
EOF
)

ISSUE_004_BODY=$(cat <<'EOF'
Criar detalhamento de iniciativas via planos.

## Checklist
- Criar tabela `plans`
- Vincular com `initiative`
- CRUD FastAPI
- Testes de integridade relacional

## Dependencia
- Depende da Issue #003
EOF
)

ISSUE_005_BODY=$(cat <<'EOF'
Criar entidade de tarefas com integracao ao OPERA.

## Checklist
- Criar tabela `tasks`
- Campos: `assigned_to`, `status`, `priority`
- Integracao com OPERA
- CRUD FastAPI
- Testes basicos

## Dependencia
- Depende da Issue #004
EOF
)

ISSUE_006_BODY=$(cat <<'EOF'
Configurar integracao base com NATS para eventos estrategicos.

## Checklist
- Configurar client NATS
- Criar publisher padrao
- Criar subscriber base
- Testes de publicacao e assinatura

## Dependencia
- Recomendado apos Issue #001
EOF
)

ISSUE_007_BODY=$(cat <<'EOF'
Definir e publicar eventos estrategicos do modulo.

## Eventos
- `strategy.created`
- `initiative.created`
- `plan.created`
- `task.generated`

## Checklist
- Definir contratos de payload
- Publicar eventos nos pontos de criacao
- Cobrir com testes de contrato

## Dependencia
- Depende da Issue #006
EOF
)

ISSUE_008_BODY=$(cat <<'EOF'
Criar dispatcher para rotear iniciativas aos monolitos.

## Checklist
- Criar engine de roteamento
- Mapear destinos: P&D, Academia, OPERA, HUB, CEFEIDA
- Regras configuraveis por tipo de iniciativa
- Testes de roteamento

## Dependencia
- Depende das Issues #006 e #007
EOF
)

ISSUE_009_BODY=$(cat <<'EOF'
Implementar geracao automatica de tasks por iniciativa.

## Checklist
- Criar logica de desdobramento
- Definir templates por tipo de iniciativa
- Garantir idempotencia
- Testes de geracao

## Dependencia
- Depende da Issue #005
EOF
)

ISSUE_010_BODY=$(cat <<'EOF'
Integrar com Academia para trilhas de treinamento.

## Checklist
- Gerar evento `training.required`
- Vincular com trilhas da Academia
- Persistir status de cumprimento
- Testes de integracao

## Dependencia
- Depende da Issue #009
EOF
)

ISSUE_011_BODY=$(cat <<'EOF'
Integrar com P&D para criacao automatica de processos.

## Checklist
- Criacao automatica de processos
- Implementar versionamento
- Registrar historico de versoes
- Testes de fluxo

## Dependencia
- Depende da Issue #009
EOF
)

ISSUE_012_BODY=$(cat <<'EOF'
Criar estrutura de Kanban estrategico no backend.

## Status padrao
- `backlog`
- `planning`
- `executing`
- `validating`
- `done`

## Checklist
- Estrutura de board no backend
- Regras de transicao de status
- Testes de transicao
EOF
)

ISSUE_013_BODY=$(cat <<'EOF'
Criar API Kanban com endpoint de board e filtros.

## Checklist
- Criar endpoint `board`
- Filtros por: `portfolio`, `monolito`, `ator`
- Paginar e ordenar resultados
- Testes de filtros

## Dependencia
- Depende da Issue #012
EOF
)

ISSUE_014_BODY=$(cat <<'EOF'
Construir dashboard estrategico no frontend React.

## Checklist
- Visao geral estrategica
- Exibir metricas
- Exibir alertas de risco e prazo
- Integrar com backend

## Dependencia
- Recomendado apos Issue #013
EOF
)

ISSUE_015_BODY=$(cat <<'EOF'
Construir Kanban geral no frontend com drag and drop.

## Checklist
- Implementar drag and drop
- Filtros dinamicos
- Sincronizacao com backend
- Testes de interacao

## Dependencia
- Depende das Issues #013 e #014
EOF
)

ISSUE_016_BODY=$(cat <<'EOF'
Criar tela de estrategia com hierarquia completa.

## Checklist
- Criar estrategia
- Visualizar hierarquia (strategy > objectives > initiatives > plans > tasks)
- Integrar com APIs do modulo
- Testes basicos de fluxo

## Dependencia
- Depende das entidades do Epic 1
EOF
)

ISSUE_017_BODY=$(cat <<'EOF'
Implementar RBAC para o modulo estrategico.

## Perfis
- `executivo`
- `gestor`
- `operacional`

## Checklist
- Definir matriz de permissao
- Aplicar autorizacao nas APIs
- Testes de autorizacao
EOF
)

ISSUE_018_BODY=$(cat <<'EOF'
Implementar auditoria completa do modulo.

## Checklist
- Registrar logs completos
- Registrar historico de mudancas
- Rastrear ator, timestamp e acao
- Testes de auditoria

## Dependencia
- Recomendado apos Issue #017
EOF
)

ISSUE_019_BODY=$(cat <<'EOF'
Implementar multi-tenant para separacao ecossistema vs cliente.

## Checklist
- Isolamento por tenant
- Escopo tenant-aware em consultas
- Escopo tenant-aware em eventos
- Testes de isolamento

## Dependencia
- Recomendado apos Issue #017
EOF
)

ISSUE_020_BODY=$(cat <<'EOF'
Implementar sugestoes via John para analise e priorizacao estrategica.

## Checklist
- Analise automatica de estrategia
- Sugestoes de priorizacao
- Integracao com dados de contexto
- Testes de contrato e fallback

## Dependencia
- Recomendado apos Epics 1 a 6
EOF
)

echo "Criando issues no repositorio: $REPO"

create_issue "[EPIC 1][001] Criar entidade Strategy" "modulo:planejamento-estrategico,epic:core,backend,database,api" "$ISSUE_001_BODY"
create_issue "[EPIC 1][002] Criar entidade Objectives (OKR)" "modulo:planejamento-estrategico,epic:core,backend,database,api" "$ISSUE_002_BODY"
create_issue "[EPIC 1][003] Criar entidade Initiatives" "modulo:planejamento-estrategico,epic:core,backend,database,api" "$ISSUE_003_BODY"
create_issue "[EPIC 1][004] Criar entidade Plans" "modulo:planejamento-estrategico,epic:core,backend,database,api" "$ISSUE_004_BODY"
create_issue "[EPIC 1][005] Criar entidade Tasks" "modulo:planejamento-estrategico,epic:core,backend,database,api,integration" "$ISSUE_005_BODY"

create_issue "[EPIC 2][006] Integracao com NATS" "modulo:planejamento-estrategico,epic:integracao,backend,integration" "$ISSUE_006_BODY"
create_issue "[EPIC 2][007] Eventos estrategicos" "modulo:planejamento-estrategico,epic:integracao,backend,integration,api" "$ISSUE_007_BODY"
create_issue "[EPIC 2][008] Dispatcher de iniciativas" "modulo:planejamento-estrategico,epic:integracao,backend,integration" "$ISSUE_008_BODY"

create_issue "[EPIC 3][009] Geracao automatica de tasks" "modulo:planejamento-estrategico,epic:execucao,backend,api" "$ISSUE_009_BODY"
create_issue "[EPIC 3][010] Integracao com Academia" "modulo:planejamento-estrategico,epic:execucao,backend,integration" "$ISSUE_010_BODY"
create_issue "[EPIC 3][011] Integracao com P&D" "modulo:planejamento-estrategico,epic:execucao,backend,integration" "$ISSUE_011_BODY"

create_issue "[EPIC 4][012] Estrutura Kanban backend" "modulo:planejamento-estrategico,epic:kanban,backend,api" "$ISSUE_012_BODY"
create_issue "[EPIC 4][013] API Kanban" "modulo:planejamento-estrategico,epic:kanban,backend,api" "$ISSUE_013_BODY"

create_issue "[EPIC 5][014] Dashboard estrategico" "modulo:planejamento-estrategico,epic:frontend,frontend,api" "$ISSUE_014_BODY"
create_issue "[EPIC 5][015] Kanban geral" "modulo:planejamento-estrategico,epic:frontend,frontend,api" "$ISSUE_015_BODY"
create_issue "[EPIC 5][016] Tela de estrategia" "modulo:planejamento-estrategico,epic:frontend,frontend,api" "$ISSUE_016_BODY"

create_issue "[EPIC 6][017] RBAC" "modulo:planejamento-estrategico,epic:governanca,backend,security" "$ISSUE_017_BODY"
create_issue "[EPIC 6][018] Auditoria" "modulo:planejamento-estrategico,epic:governanca,backend,security" "$ISSUE_018_BODY"
create_issue "[EPIC 6][019] Multi-tenant" "modulo:planejamento-estrategico,epic:governanca,backend,security" "$ISSUE_019_BODY"

create_issue "[EPIC 7][020] Sugestoes via John" "modulo:planejamento-estrategico,epic:inteligencia,backend,ai" "$ISSUE_020_BODY"

echo "Concluido: 20 issues criadas com milestone '$MILESTONE'."
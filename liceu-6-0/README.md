# LICEU 6.0 - PRODUCAO TOTAL LOCAL

Tudo e evento. Tudo passa pelo CORE-DNA. Nenhum monolito decide sozinho.

Backlog mestre de execucao: [MASTER_ISSUES.md](MASTER_ISSUES.md).

## Topologia real

```text
LICEU 6.0 CORE (runtime + SDK)
  -> CORE-DNA
  -> EVENT BUS (NATS)
  -> Archimedes / JuridicoTech / HubBackoffice / GameMKT / John
```

Estrutura operacional:

```text
liceu-6.0/
├── core-sdk/
├── runtime/
├── event-registry/
├── monolitos/
│   ├── archimedes/
│   ├── juridicotech/
│   ├── hubbackoffice/
│   ├── gamemkt/
│   ├── john/
│   └── ...
├── infra/
│   ├── docker-compose.yml
│   ├── kong/
│   ├── nats/
│   ├── postgres/
│   └── redis/
├── observability/
│   ├── grafana/
│   ├── prometheus/
│   └── loki/
└── .env
```

## 1) Build do CORE-DNA

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/liceu-6.0/core-sdk
chmod +x scripts/build_dna.sh
./scripts/build_dna.sh
```

## 2) Subir a stack local

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/liceu-6.0/infra
docker compose up -d --build
```

Os servicos Python agora sobem com dependencias pré-instaladas nas imagens; nao ha mais instalacao via pip a cada restart.

Servicos expostos:
- postgres em localhost:5432
- redis em localhost:6380
- nats em localhost:4222 e monitor em localhost:8222
- kong proxy em localhost:8000 e admin em localhost:8001
- archimedes_api em localhost:8010
- archimedes_web em localhost:5173
- grafana em localhost:3000
- prometheus em localhost:9090
- loki em localhost:3100

## 3) Publicar fluxo canonico

Evento de boot:

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/liceu-6.0/core-sdk
PYTHONPATH=. python3 scripts/publish_boot_event.py
```

Fluxo Archimedes -> JuridicoTech -> HubBackoffice -> GameMKT:

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/liceu-6.0/core-sdk
PYTHONPATH=. python3 scripts/publish_demo_flow.py
```

## 4) Validacao rapida

```bash
docker logs -f liceu_runtime
docker logs -f liceu_juridicotech
docker logs -f liceu_hubbackoffice
docker logs -f liceu_gamemkt
docker logs -f liceu_john
```

Rotas uteis:
- Kong para Archimedes: http://localhost:8000/archimedes
- Kong para monitor do NATS: http://localhost:8000/nats
- NATS monitor direto: http://localhost:8222

## 5) Contratos canonicos

- CORE-DNA: core_dna/events.proto
- Registry unico: event-registry/events.json
- SDK compartilhado: core-sdk/sdk/event_bus.py
- Artefatos gerados: core-sdk/generated/python, core-sdk/generated/typescript e core-sdk/generated/jsonschema

## Alertas reais

1. Se um monolito publicar fora de liceu.events, voce perde rastreabilidade.
2. Se um handler duplicar regra fora do SDK, voce cria divergencia silenciosa.
3. Observabilidade sem instrumentacao de aplicacao ainda e scaffold; os proximos passos sao expor metricas por monolito e dashboards operacionais.

## 6) Governanca de acesso (RBAC)

Modelo oficial do ecossistema para evitar acesso amplo sem rastreabilidade.

### Papeis canonicos
- SUPER_ADMIN
- DIRETOR
- FINANCEIRO
- ENGENHARIA
- QUALIDADE
- AUDITOR
- GERENTE
- FORNECEDOR
- CLIENTE
- COLABORADOR

### Hierarquia e escopo de monolitos
- SUPER_ADMIN: topo da hierarquia, visao total, aprova decisoes do John IA, cria estrategias e libera capital.
  Monolitos: LICEU CORE + todos.
- DIRETOR ESTRATEGICO: portfolio, indicadores macro e simulacoes, aprova projetos e define prioridades.
  Monolitos: LICEU + ECONOTECH + CEFEIDA.
- FINANCEIRO: DRE, fluxo de caixa e investimentos, libera pagamentos e ajusta orcamento.
  Monolitos: HUB + CEA.
- ENGENHARIA: obras, cronogramas e performance, decide tecnicamente e redistribui recursos.
  Monolitos: OPERA + BIM/ENG.
- QUALIDADE (P&D): processos, auditorias e nao conformidades, altera processos e define padroes.
  Monolitos: P&D + ANCHOR.
- AUDITOR/HOSPITAL: saude das empresas, riscos e falhas, abre intervencao e bloqueia operacao.
  Monolitos: AUDIT + HOSPITAL.
- GERENTE: obra, equipe e tarefas, executa projeto e reporta progresso.
  Monolitos: OPERA.
- FORNECEDOR: pedidos, contratos e demandas, entrega e atualiza capacidade.
  Monolitos: FORNECEDORES.
- CLIENTE: projeto proprio, status e documentos, acompanha e aprova etapas.
  Monolitos: ARCHIMEDES / OPERA.
- COLABORADOR/APRENDIZ: treinamentos e tarefas atribuidas, executa atividades e aprende processos.
  Monolitos: ACADEMIA + OPERA.

### Matriz simplificada
- aprovar estrategia: SUPER_ADMIN + DIRETOR
- liberar pagamento: FINANCEIRO
- executar obra: GERENTE
- alterar processo: QUALIDADE
- ver tudo: SUPER_ADMIN

### Endpoints de governanca no backend core
- GET /governance/roles
- POST /governance/approve-strategy
- POST /governance/release-payment
- POST /governance/execute-work
- POST /governance/change-process
- POST /governance/approve-john

Regra de ouro: quanto maior o poder, menor o numero de usuarios.

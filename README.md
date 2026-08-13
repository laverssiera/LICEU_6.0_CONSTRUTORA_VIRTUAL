## GUIA TECNICO RAPIDO

Documentacao operacional unificada para todo o ecossistema. Cada modulo segue padrao: objetivo, execucao, validacao.

### Pontos de entrada principais

| Documento | Proposito | Local |
|-----------|-----------|-------|
| Stack e infraestrutura | Criar ambiente completo (NATS, banco, cache) | [liceu-6.0/README.md](liceu-6.0/README.md) |
| First Flow Runbook | Fluxo E2E de negocio (governance até business case) | [cv-backend-core/FIRST_FLOW_RUNBOOK.md](cv-backend-core/FIRST_FLOW_RUNBOOK.md) |
| Planet Runtime Endpoint | Disparo HTTP do runtime planetario e payloads | [runtime/documentation/planetary/planet_runtime_endpoint.md](runtime/documentation/planetary/planet_runtime_endpoint.md) |
| Demo automática VS Code | Executar primeiro fluxo via task | `CV Backend: Demo First Flow` |
| **John — IA Interpretativa** | **Arquitetura completa, CRM + Sales Dev Rep** | **[JOHN_ARCHITECTURE.md](JOHN_ARCHITECTURE.md)** |

### Módulos - Monolitos e Serviços

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **Archimedes** | [liceu-6.0/monolitos/archimedes/README.md](liceu-6.0/monolitos/archimedes/README.md) | Publisher de lead e deal |
| **JuridicoTech** | [liceu-6.0/juridicotech/README.md](liceu-6.0/juridicotech/README.md) | Listener de eventos juridicos |
| **HubBackoffice** | [liceu-6.0/hubbackoffice/README.md](liceu-6.0/hubbackoffice/README.md) | Listener de eventos financeiros |
| **Core SDK** | [liceu-6.0/core-sdk/README.md](liceu-6.0/core-sdk/README.md) | Build de protos, event bus compartilhado |

### Núcleo Compartilhado - Liceu-6-0

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **Runtime** | [liceu-6-0/runtime/README.md](liceu-6-0/runtime/README.md) | Orquestracao de fluxos multi-etapa |
| **SDK** | [liceu-6-0/sdk/README.md](liceu-6-0/sdk/README.md) | API centralizada de analise e decisao |
| **Stream Bus** | [liceu-6-0/stream-bus/README.md](liceu-6-0/stream-bus/README.md) | Event Bus NATS com desacoplamento total |

### Frontend - Assets

| Recurso | Arquivo | Uso |
|---------|---------|-----|
| Video Institucional | [cv-frontend/public/videos/README.md](cv-frontend/public/videos/README.md) | Hero com videos desktop/mobile |
| Video de Investidores | [frontend/public/videos/README.md](frontend/public/videos/README.md) | Rota /investidores |

### Frontend x Backend (cv-frontend)

Configuracao recomendada:

1. Copiar [cv-frontend/.env.example](cv-frontend/.env.example) para `.env` no mesmo diretorio.
2. Escolher modo de conexao:
- Proxy local (recomendado em dev): deixar `VITE_API_BASE_URL` vazio e definir `VITE_PROXY_TARGET=http://127.0.0.1:8000`.
- URL direta: definir `VITE_API_BASE_URL` com o host do backend (exemplo `http://127.0.0.1:8000`).
3. Subir frontend com `npm run dev` em [cv-frontend](cv-frontend).

Rotas do Investor Relations no gateway central:

- GET `/gateway/investor-relations/routes`
- GET `/gateway/investor-relations/health`
- GET `/gateway/investor-relations/dashboard`
- GET `/gateway/investor-relations/events/published`
- POST `/gateway/investor-relations/investors`
- POST `/gateway/investor-relations/opportunities`
- POST `/gateway/investor-relations/events/consume`
- POST `/gateway/investor-relations/allocations`
- POST `/gateway/investor-relations/performance`

### Sequencia recomendada para homologacao

1. **Setup local** → Abrir [liceu-6.0/README.md](liceu-6.0/README.md), seguir build do CORE-DNA e levantar `docker compose up -d`.
2. **Demo manual** → Executar task `CV Backend: Demo First Flow` ou rodar manualmente as etapas do runbook.
3. **Validacao de eventos** → Deixar listeners (JuridicoTech, HubBackoffice) ativos e confirmar fluxo completo.
4. **Inspecao** → Conferir timeline de business cases, auditoria e fechamento.

### Padrão de documentação

Todos os READMEs técnicos seguem este modelo:
- **Objetivo**: Por quê este módulo existe
- **Estrutura**: Arquivos e responsabilidades
- **Requisitos**: Dependências obrigatórias
- **Execução**: Commands prontos para rodar
- **Validação**: Checklist para confirmar funcionamento
- **Variáveis de ambiente**: Customizações esperadas
- **Observações**: Armadilhas e regras de ouro

## PLANEJAMENTO 3, 5 E 10 ANOS

### Resumo Executivo

#### 3 anos — Validacao

Foco:
- Portfolio 3 (servicos)
- Primeiras obras comuns

Objetivos:
- Validar o sistema
- Gerar dados reais
- Padronizar processos

Resultado esperado:
- Produto funcionando com operacao real

#### 5 anos — Escala

Foco:
- Obras comuns em escala
- Plataforma como produto

Objetivos:
- Expansao regional
- Fornecedores integrados
- OPERA + CEFEIDA como SaaS

Resultado esperado:
- Empresa + plataforma + rede

#### 10 anos — Dominancia

Foco:
- Expansao global
- Obras pesadas completas

Objetivos:
- Infraestrutura pesada
- Sistema semi-autonomo
- Economia integrada

Resultado esperado:
- Plataforma dominante global

## O QUE FAZER AGORA

Sem romantizar: esta e a sequencia pratica que move o jogo.

### Prioridade 1 — Planejamento Estrategico

Comecar por esse modulo foi a decisao correta porque ele:
- Cria direcao
- Organiza o caos
- Conecta tudo

### Prioridade 2 — Teste de Integracao

Minimo viavel:
- Planejamento -> OPERA -> P&D -> Academia

Se esse fluxo rodar de ponta a ponta, o sistema esta vivo.

### Prioridade 3 — Portfolio 3

Meta imediata:
- Vender 1 servico real
- Rodar esse servico dentro do sistema

### Prioridade 4 — Dados

Meta imediata:
- Estruturar o codigo-mae
- Garantir rastreabilidade

### Prioridade 5 — Time Inicial

Composicao minima:
- Engenharia
- Tech
- Comercial
- Financeiro

## Alerta Final

O ponto atual e sensivel: muito poder acumulado com pouca execucao real.

Regra de ouro daqui para frente:
- Cada nova feature precisa ser testada no mundo real

## MODELO DE GOVERNANCA

### Principio

Toda decisao estrategica precisa virar objeto no sistema.

Nada relevante pode ficar apenas em reuniao, chat ou alinhamento verbal sem registro estruturado.

### Dominios da Governanca

Governance Core:
- OKR / KPI
- DRE / Financeiro
- Reunioes / Rituais
- Novos Negocios
- Auditoria / Compliance

## KANBAN DE NOVOS NEGOCIOS

Esse pipeline deve ser o coracao da alta direcao.

### Colunas oficiais

1. Ideia / Produto
2. Estudo Tecnico
3. Viabilidade Financeira
4. SWOT / BSG
5. Analise de Mercado
6. Market Share
7. Comite de Aprovacao
8. Aprovado / Reprovado
9. Termo de Abertura
10. Piloto
11. Licoes Aprendidas
12. Escala
13. Payback
14. Retorno
15. Business Case
16. Banco de Casos

### Regra

Nenhum projeto entra no ecossistema sem passar por esse kanban.

### Exemplo de card

```json
{
	"title": "Empreendimento 20 casas",
### Inteligência & CRM (John)

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **John CRM** | [modules/crm/README.md](modules/crm/README.md) | Sales Dev Rep — qualifica leads |
| **John Engine** | [liceu-6.0/runtime/john_engine/README.md](liceu-6.0/runtime/john_engine/README.md) | Interpreta eventos, gera recomendacoes |
| **CRM Schema** | [modules/crm/schema.sql](modules/crm/schema.sql) | Banco de dados de leads |
	"portfolio": "Obras Comuns",
### Núcleo Compartilhado - Liceu-6-0
	"program": "Residencial",
	"stage": "Viabilidade Financeira",
	"owner": "Diretoria Engenharia",
	"estimated_cost": 2000000,
	"expected_return": 3200000,
	"risk_level": "medium"
}
```

## INTEGRACAO COM O ECOSSISTEMA

Quando um item muda para Termo de Abertura, o sistema deve disparar automaticamente:
- Criacao do projeto no OPERA
- Criacao da estrutura no P&D
- Criacao do plano financeiro no HUB
- Geracao do acompanhamento no Planejamento Estrategico

## GOVERNANCA FINANCEIRA

### DRE base

- Receita
- (-) Custos
- (-) Despesas
- (=) Resultado

### Estrutura de dados sugerida

```sql
dre_entries (
	id,
	project_id,
	type,
	value,
	date
)
```

### KPIs financeiros

- Margem
- Payback
- ROI
- Fluxo de caixa

## OKR E KPI

### Estrutura OKR

```sql
okrs (
	id,
	objective,
	key_result,
	target,
	current_value
)
```

### Estrutura KPI

```sql
kpis (
	id,
	name,
	value,
	target,
	unit
)
```

## CALENDARIO DE GOVERNANCA

### Rituais

- Diario: operacao no OPERA
- Semanal: gestores e acompanhamento de projetos
- Mensal: diretoria com DRE e KPIs
- Trimestral: estrategia e OKRs
- Anual: planejamento global

### Estrutura de dados sugerida

```sql
meetings (
	id,
	type,
	date,
	participants,
	notes
)
```

## FEIRAS E NETWORKING

```sql
events (
	id,
	name,
	type,
	location,
	date,
	strategic_value
)
```

## COMPLIANCE E AUDITORIA

```sql
audits (
	id,
	project_id,
	status,
	findings,
	action_required
)
```

Regra:
- Todo projeto aprovado precisa de trilha de auditoria.

## BANCO DE CONHECIMENTO

Esse modulo fecha o loop de aprendizagem do ecossistema.

```sql
business_cases (
	id,
	project_id,
	lessons_learned,
	roi,
	duration,
	success_flag
)
```

Uso previsto:
- Alimentar P&D
- Melhorar decisoes futuras
- Servir como base do John

## EPIC — GOVERNANCE CORE

Issues sugeridas:
- Issue #101 — Criar modulo Governance
- Issue #102 — Kanban Novos Negocios
- Issue #103 — Engine de transicao de fases
- Issue #104 — Integracao com OPERA / P&D / HUB
- Issue #105 — Modulo OKR/KPI
- Issue #106 — Modulo DRE
- Issue #107 — Calendario de governanca
- Issue #108 — Compliance e auditoria
- Issue #109 — Banco de business cases
- Issue #110 — RBAC de alta direcao

## Ponto Critico

Se a governanca for mal desenhada:
- Vira burocracia
- Trava o sistema

Regra de ouro:
- Governanca deve acelerar decisao, nao travar

## AUDITORIA CONTINUA E HOSPITAL DE EMPRESAS

### Conceito Central

O ecossistema passa a operar com dois sistemas conectados:
- Auditoria Continua: controle, deteccao, melhoria e prevencao
- Hospital de Empresas: cuidado, recuperacao, evolucao e elegibilidade

Fluxo estrutural:
- Auditoria detecta
- Hospital trata
- P&D aprende
- Academia treina

## MODULO DE AUDITORIA CONTINUA

### Proposito

Monitorar -> detectar -> corrigir -> aprender -> prevenir

### Dominios de auditoria

- Operacional (OPERA)
- Financeiro (HUB / CEA)
- Processos (P&D)
- Tecnologia (codigo / sistemas)
- Comercial (vendas / contratos)
- Compliance (juridico / governanca)
- Fornecedores (capacidade / entrega)

### Fluxo base

1. Um evento acontece no ecossistema
2. O motor de auditoria analisa esse evento
3. O sistema gera um finding
4. O risco e classificado
5. O sistema aciona task, treinamento ou ajuste de processo

### Classificacao de severidade

- LOW: melhoria leve
- MEDIUM: ajuste necessario
- HIGH: acao imediata
- CRITICAL: bloqueio e escalonamento

### Estrutura de dados sugerida

```sql
audit_events (
	id,
	source,
	entity_id,
	type,
	severity,
	description,
	detected_at
)

audit_actions (
	id,
	audit_id,
	action_type,
	assigned_to,
	status
)
```

### Inteligencia esperada

Quando o erro se repete, ele deixa de ser incidente isolado e vira problema estrutural.

Desdobramento esperado:
- P&D atualiza processo
- Academia gera treinamento obrigatorio
- A recorrencia passa a ser monitorada como risco sistemico

## MODULO HOSPITAL DE EMPRESAS

### Proposito

Manter empresas do ecossistema saudaveis, produtivas e confiaveis.

### Visao operacional

Cada empresa precisa ter um score dinamico de saude.

### Dimensoes de saude

- Financeira
- Operacional
- Tecnica
- Governanca
- Comercial
- Cultural
- Tecnologica

### Exemplo de score

```json
{
	"empresa": "Fornecedor X",
	"health_score": 78,
	"finance": 80,
	"operational": 70,
	"compliance": 90,
	"risk": "medium"
}
```

### Tipos de intervencao

- Preventivo: auditorias leves e recomendacoes
- Corretivo: ajuste de processo e treinamento obrigatorio
- Preditivo: detectar tendencia de falha e agir antes do problema

### Fluxo do hospital

1. A empresa entra no ecossistema
2. O monitoramento continuo atualiza o score
3. Se o score cair, o sistema cria plano de recuperacao, treinamento e intervencao
4. Se o score subir, a empresa pode se tornar elegivel para investimento

## INTEGRACAO COM INVESTIMENTOS

Relacao com CEA:
- Score alto: elegivel para investimento
- Score medio: acompanhamento ativo
- Score baixo: intervencao obrigatoria
- Score critico: restricao no ecossistema

## PROTECAO CONTRA DESONESTOS

Camadas de protecao:
- Score dinamico dificil de manipular
- Auditoria cruzada entre varios monolitos
- Historico imutavel de logs
- Flags de risco para fraude, inadimplencia e inconsistencias

### Base minima de log imutavel

```sql
audit_logs (
	id,
	entity,
	action,
	timestamp
)
```

## INTEGRACAO COM ACADEMIA

Toda falha relevante deve gerar treinamento direcionado.

Exemplo operacional:
- Erro recorrente em obra
- P&D ajusta processo
- Academia cria curso
- Equipe executa treinamento obrigatorio

## INTEGRACAO COM P&D

Fluxo esperado:
- Auditoria identifica falha
- P&D corrige o processo
- Nova versao do processo e aplicada no ecossistema

## INTEGRACAO COM PLANEJAMENTO

Problemas recorrentes nao podem morrer em backlog tecnico.

Regra:
- Recorrencia relevante vira iniciativa estrategica
- Impacto sistemico sobe para Planejamento Estrategico
- Aprendizado consolidado volta para governanca, P&D e Academia

## ISSUES GITHUB — AUDITORIA E HOSPITAL DE EMPRESAS

### Ordem recomendada de execucao

1. Issue #202 — Eventos de auditoria
2. Issue #201 — Motor de auditoria
3. Issue #203 — Classificacao de risco
4. Issue #204 — Geracao de acoes
5. Issue #209 — Logs imutaveis
6. Issue #210 — Flags de risco
7. Issue #205 — Modelo de health score
8. Issue #206 — Dashboard de saude
9. Issue #207 — Plano de recuperacao
10. Issue #208 — Integracao com CEA

### EPIC — AUDITORIA CONTINUA

#### Issue #201 — Motor de auditoria

Objetivo:
- Criar a engine central de analise para transformar eventos operacionais em findings auditaveis.

Escopo:
- Receber eventos normalizados
- Aplicar regras basicas por dominio
- Gerar findings estruturados

Criterios de aceite:
- Existe um servico unico para avaliar eventos de auditoria
- O servico suporta pelo menos os dominios operacional, financeiro e compliance
- Cada avaliacao gera um finding com source, entity_id, type, severity e description
- O motor e testado com cenarios LOW, MEDIUM, HIGH e CRITICAL

Dependencias:
- Issue #202

#### Issue #202 — Eventos de auditoria

Objetivo:
- Padronizar a entrada de eventos dos monolitos para o modulo de auditoria continua.

Escopo:
- Capturar eventos de OPERA, HUB, P&D, comercial e compliance
- Definir envelope canonico de auditoria
- Garantir rastreabilidade por origem

Criterios de aceite:
- Existe um schema unico para audit_events
- Eventos de pelo menos 3 monolitos entram no pipeline no mesmo formato
- Cada evento possui source, entity_id, timestamp e payload auditavel
- O pipeline rejeita ou marca eventos invalidos

Dependencias:
- Nenhuma

#### Issue #203 — Classificacao de risco

Objetivo:
- Implementar o algoritmo de severity para findings de auditoria.

Escopo:
- Traduzir regras de negocio em LOW, MEDIUM, HIGH e CRITICAL
- Considerar recorrencia, impacto e dominio

Criterios de aceite:
- Existe funcao ou servico dedicado para classificar severity
- A classificacao considera pelo menos impacto, recorrencia e origem
- Findings repetidos aumentam severidade quando aplicavel
- Casos de teste cobrem a progressao de risco

Dependencias:
- Issue #201

#### Issue #204 — Geracao de acoes

Objetivo:
- Converter findings validados em respostas operacionais automaticas.

Escopo:
- Gerar task
- Gerar treinamento obrigatorio
- Gerar ajuste de processo

Criterios de aceite:
- Finding MEDIUM ou superior pode gerar task automatica
- Finding recorrente pode gerar acao de processo para P&D
- Finding aderente a capacitação pode gerar acao de treinamento para Academia
- As acoes ficam registradas em audit_actions com status rastreavel

Dependencias:
- Issue #201
- Issue #203

### EPIC — HOSPITAL DE EMPRESAS

#### Issue #205 — Modelo de health score

Objetivo:
- Definir e calcular automaticamente o score de saude de empresas do ecossistema.

Escopo:
- Modelar metricas por dimensao
- Calcular score consolidado
- Expor classificacao de risco

Criterios de aceite:
- Existe modelo de score por empresa
- O score contempla pelo menos dimensoes financeira, operacional, compliance e tecnologica
- O calculo e reproduzivel e testado
- O resultado traz score final e risco associado

Dependencias:
- Issue #201
- Issue #203

#### Issue #206 — Dashboard de saude

Objetivo:
- Exibir a visao consolidada de saude das empresas com historico e tendencia.

Escopo:
- Painel por empresa
- Historico de score
- Visao de risco atual

Criterios de aceite:
- Existe endpoint ou view para listar scores por empresa
- Cada empresa exibe score atual, risco e historico minimo
- O dashboard destaca empresas em deterioracao
- A consulta suporta filtro por risco e periodo

Dependencias:
- Issue #205

#### Issue #207 — Plano de recuperacao

Objetivo:
- Gerar e acompanhar automaticamente um plano de recuperacao quando o score cair.

Escopo:
- Criar plano de intervencao
- Associar acoes corretivas
- Acompanhar evolucao do score

Criterios de aceite:
- Empresas abaixo do threshold geram plano de recuperacao
- O plano inclui responsavel, prazo e lista de acoes
- O sistema acompanha evolucao do score apos a intervencao
- Existe status de plano em andamento, concluido ou agravado

Dependencias:
- Issue #204
- Issue #205

#### Issue #208 — Integracao com CEA

Objetivo:
- Conectar score de saude com elegibilidade de investimento no ecossistema financeiro.

Escopo:
- Liberar elegibilidade para score alto
- Aplicar acompanhamento para score medio
- Restringir casos criticos

Criterios de aceite:
- Empresas com score alto podem ser marcadas como elegiveis para investimento
- Empresas com score medio entram em acompanhamento
- Empresas com score baixo ou critico recebem bloqueio ou restricao configuravel
- A decisao fica rastreada para auditoria

Dependencias:
- Issue #205
- Issue #206

### EPIC — SEGURANCA E COMPLIANCE

#### Issue #209 — Logs imutaveis

Objetivo:
- Garantir trilha completa e imutavel das acoes criticas do modulo.

Escopo:
- Persistir eventos e acoes com carimbo temporal
- Evitar alteracao silenciosa de historico
- Facilitar auditoria retroativa

Criterios de aceite:
- Todas as acoes criticas geram log imutavel
- O log guarda entity, action, actor e timestamp
- O historico pode ser consultado sem perder encadeamento temporal
- Existe cobertura de teste para persistencia e consulta

Dependencias:
- Issue #202

#### Issue #210 — Flags de risco

Objetivo:
- Criar sistema de flags para fraude, inadimplencia e inconsistencia programatica ou operacional.

Escopo:
- Detectar fraude suspeita
- Detectar inconsistencias de dados
- Sinalizar entidades com comportamento de risco

Criterios de aceite:
- Existe modelo para flags de risco associado a empresa, projeto ou evento
- O sistema suporta ao menos fraude, inadimplencia e inconsistencia
- Flags podem elevar severity ou restringir fluxo no ecossistema
- Flags ficam visiveis para auditoria e hospital de empresas

Dependencias:
- Issue #203
- Issue #209

### Estrutura pronta para GitHub

Padrao sugerido para criacao:
- Titulo: usar exatamente o nome da issue acima
- Labels: epic:auditoria, epic:hospital, epic:compliance, backend, governance
- Milestone sugerida: Auditoria Continua e Hospital de Empresas
- Formato de descricao: Objetivo + Escopo + Criterios de aceite + Dependencias

## 🧱 FASE 1 — BOOTSTRAP DO REPOSITÓRIO
📦 Criar estrutura oficial
liceu-6-0-core-sdk/
📁 Estrutura final obrigatória
├── core_dna/                # 📦 Protobuf (Single Source of Truth)
├── brain_lib/               # 🧠 FP Engine (CEFEIDA + JOHN logic)
├── stream_bus/              # ⚡ Event Backbone (NATS)
├── factory_entities/        # 🏗️ Domain Layer (POO leve)
├── sdk/                     # 🌐 Public API Layer
├── runtime/                 # 🔥 Orchestrator Engine
├── governance/              # 🔐 RBAC + 6 USERS SYSTEM
├── contracts/               # ⚖️ IMOB DIGITAL 6.0 RULES
├── tests/                   # 🧪 Full Coverage Tests
├── scripts/                 # 🧰 Build + Compile + Deploy
├── docker/                  # 🐳 NATS + Infra stack
└── ci/                      # ⚙️ GitHub Actions pipelines

## 🧬 FASE 2 — CORE-DNA (SINGLE SOURCE OF TRUTH)
📌 REGRA ABSOLUTA

Todo dado entre sistemas:

→ PASSA OBRIGATORIAMENTE POR CORE-DNA

🏠 PROPERTY CONTRACT
```proto
syntax = "proto3";

package liceu.core;

message Property {
  string id = 1;
    string title = 2;
	  string type = 3;
	    double price = 4;
		  double rent_value = 5;
		    double area = 6;
			  string location = 7;
			    string owner_id = 8;
				  string status = 9;
				    string created_at = 10;
					}
					```
					📡 EVENT ENVELOPE (UNIVERSAL SYSTEM BUS)
					```proto
					syntax = "proto3";

					package liceu.core;

					message EventEnvelope {
					  string id = 1;
					    string type = 2;
						  string source = 3;
						    string timestamp = 4;
							  string tenant = 5;
							    string correlation_id = 6;
								  string payload = 7;
								  }
								  ```

								  ## 🧠 FASE 3 — BRAIN-LIB (FUNCTIONAL ENGINE)
								  📌 REGRA
								  ❌ sem estado
								  ❌ sem banco
								  ❌ sem side effects
								  ✅ apenas transformação pura
								  📊 FINANCE ENGINE
								  ```python
								  from dataclasses import dataclass

								  @dataclass(frozen=True)
								  class FinanceInput:
																	   price: float
																	   rent: float

										def cap_rate(fin: FinanceInput) -> float:
											return 0 if fin.price == 0 else (fin.rent * 12) / fin.price * 100

											def risk_band(cap_rate: float) -> str:
												if cap_rate > 8:
														return "HIGH_YIELD"
															if cap_rate > 5:
																	return "STABLE"
																		return "SPECULATIVE"
																		```
																		📊 CEFEIDA ENGINE
																		```python
																		def viability_score(demand, supply, risk):
																			return (demand * 0.5) - (supply * 0.3) - (risk * 0.2)

																			def decision(score):
																				if score > 70:
																						return "APPROVED"
																							if score > 40:
																									return "REVIEW"
																										return "REJECTED"
																										```

																										## ⚡ FASE 4 — STREAM-BUS (EVENT BACKBONE)
																										📌 REGRA

																										Nenhum monólito conversa direto com outro.
																										```python
																										import asyncio
																										from nats.aio.client import Client as NATS

																										class EventBus:
																											def __init__(self):
																													self.nc = NATS()

																														async def connect(self):
																																await self.nc.connect("nats://localhost:4222")

																																	async def publish(self, topic: str, payload: dict):
																																			await self.nc.publish(topic, str(payload).encode())

																																				async def subscribe(self, topic, handler):
																																						async def wrapper(msg):
																																									await handler(msg.data.decode())

																																											await self.nc.subscribe(topic, cb=wrapper)
																																											```

																																											## 🏗️ FASE 5 — FACTORY-ENTITIES (DOMÍNIO REAL)
																																											```python
																																											from dataclasses import dataclass, field
																																											from typing import List

																																											@dataclass
																																											class SPE:
																																												id: str
																																													name: str
																																														properties: List[str] = field(default_factory=list)
																																															investors: List[str] = field(default_factory=list)
																																																status: str = "draft"

																																																	def activate(self):
																																																			self.status = "active"
																																																			```

																																																			## 🌐 FASE 6 — SDK (UNIFIED LAYER)
																																																			```python
																																																			from brain_lib.finance import FinanceInput, cap_rate, risk_band
																																																			from brain_lib.market import viability_score, decision

																																																			class LiceuSDK:
																																																				def analyze_property(self, price, rent):
																																																						cap = cap_rate(FinanceInput(price, rent))
																																																								return {
																																																											"cap_rate": cap,
																																																														"grade": risk_band(cap)
																																																																}

																																																																	def evaluate_market(self, demand, supply, risk):
																																																																			score = viability_score(demand, supply, risk)
																																																																					return {
																																																																								"score": score,
																																																																											"decision": decision(score)
																																																																													}
																																																																													```

																																																																													## 🔥 FASE 7 — RUNTIME ORCHESTRATOR
																																																																													```python
																																																																													from sdk.liceu_sdk import LiceuSDK

																																																																													class Runtime:
																																																																														def __init__(self):
																																																																																self.sdk = LiceuSDK()

																																																																																	def archimedes_flow(self, data):
																																																																																			finance = self.sdk.analyze_property(
																																																																																						data["price"], data["rent"]
																																																																																								)

																																																																																										market = self.sdk.evaluate_market(
																																																																																													data["demand"], data["supply"], data["risk"]
																																																																																															)

																																																																																																	return {
																																																																																																				"finance": finance,
																																																																																																							"market": market
																																																																																																									}
																																																																																																									```

																																																																																																									## 🔐 FASE 8 — GOVERNANCE (IMOB DIGITAL CORE)
																																																																																																									👤 6 USUÁRIOS
																																																																																																									ADMIN_MASTER
																																																																																																									BROKER
																																																																																																									CLIENT
																																																																																																									OWNER
																																																																																																									INVESTOR
																																																																																																									SYSTEM (JOHN AI)
																																																																																																									⚖️ EVENTOS JURÍDICOS
																																																																																																									contract.created
																																																																																																									contract.signed
																																																																																																									contract.locked
																																																																																																									commission.protected
																																																																																																									deal.closed
																																																																																																									bypass.detected

																																																																																																									## 🧠 FASE 9 — REGRAS INQUEBRÁVEIS
																																																																																																									FP (Brain-Lib)
																																																																																																									auditável
																																																																																																									determinístico
																																																																																																									sem estado
																																																																																																									EVENT DRIVEN (Stream-Bus)
																																																																																																									tudo é evento
																																																																																																									nada síncrono crítico
																																																																																																									ENTITIES
																																																																																																									só domínio real
																																																																																																									CORE-DNA
																																																																																																									nunca quebrar schema sem versionamento

																																																																																																									## 🏛️ FASE 10 — INTEGRAÇÃO ECOSSISTEMA
																																																																																																									ARCHIMEDES

																																																																																																									→ consome SDK + CEFEIDA + EVENTS

																																																																																																									IMOB DIGITAL 6.0

																																																																																																									→ protege contratos + comissão + jurídico

																																																																																																									JOHN BRASILEIRO

																																																																																																									→ interpreta eventos + gera scripts

																																																																																																									CEFEIDA

																																																																																																									→ 100% FP puro

																																																																																																									## 🚀 FASE FINAL — EXECUTION ORDER
																																																																																																									ORDEM DE BUILD OBRIGATÓRIA
																																																																																																									core_dna compile
																																																																																																									brain_lib validation
																																																																																																									stream_bus (NATS up)
																																																																																																									sdk generation
																																																																																																									runtime orchestration
																																																																																																									governance RBAC
																																																																																																									contract engine IMOB
																																																																																																									Archimedes plug-in
																																																																																																									# LICEU 6.0 — CORE-DNA SDK

																																																																																																									Este repositório contém o núcleo universal do ecossistema LICEU 6.0, servindo como fonte única de verdade (Single Source of Truth) para todos os monólitos e serviços.

																																																																																																									## Estrutura dos Módulos

																																																																																																									- **core-dna/**: Contratos universais em Protobuf
																																																																																																									- **brain_lib/**: Lógica funcional pura (sem estado, sem side effects)
																																																																																																									- **stream-bus/**: Event Bus reativo (NATS)
																																																																																																									- **factory_entities/**: Entidades de domínio (POO)
																																																																																																									- **sdk/**: Interface pública para monólitos
																																																																																																									- **runtime/**: Orquestrador de fluxos
																																																																																																									- **tests/**: Testes unitários

																																																																																																									---


																																																																																																									---

																																																																																																									## 🚦 ROADMAP DE IMPLEMENTAÇÃO — LICEU 6.0 CORE SDK

																																																																																																									### FASE 1 — REPO BOOTSTRAP OFICIAL (OBRIGATÓRIO)
																																																																																																									**Estrutura final obrigatória:**
																																																																																																									```
																																																																																																									liceu-6-0-core-sdk/
																																																																																																									├── core_dna/                # protobuf compiled + source
																																																																																																									├── brain_lib/               # FP engine (CEFEIDA + JOHN logic)
																																																																																																									├── stream_bus/              # NATS wrapper + event system
																																																																																																									├── factory_entities/        # SPE, Contract, User entities
																																																																																																									├── sdk/                     # public API layer (LiceuSDK)
																																																																																																									├── runtime/                 # orchestrator engine
																																																																																																									├── governance/              # auth + 6-user system + permissions
																																																																																																									├── contracts/               # juridical + IMOB DIGITAL 6.0 rules
																																																																																																									├── tests/                   # full test coverage
																																																																																																									├── scripts/                 # build + deploy + proto compile
																																																																																																									├── docker/                  # NATS + Postgres + runtime stack
																																																																																																									└── ci/                      # GitHub Actions pipelines
																																																																																																									```

																																																																																																									### FASE 2 — BUILD SYSTEM (PROTO + SDK COMPILATION)
																																																																																																									- Todo push gera automaticamente:
																																																																																																										- Python SDK
																																																																																																											- TypeScript SDK (frontend Archimedes)
																																																																																																												- JSON Schema fallback
																																																																																																													- Event registry

																																																																																																													**Script obrigatório:**  `scripts/build_dna.sh`
																																																																																																													```bash
																																																																																																													#!/bin/bash
																																																																																																													echo "Compiling CORE-DNA Protobuf..."

																																																																																																													protoc --python_out=./core_dna/compiled \
																																																																																																																 --js_out=./core_dna/compiled \
																																																																																																																 			 core_dna/*.proto

																																																																																																																			 echo "Generating SDK bindings..."

																																																																																																																			 python scripts/generate_sdk.py

																																																																																																																			 echo "DONE: LICEU 6.0 DNA BUILT"
																																																																																																																			 ```

																																																																																																																			 ### FASE 3 — EVENT SYSTEM (PRODUCTION NATS CLUSTER)
																																																																																																																			 - Dev → local NATS
																																																																																																																			 - Staging → cluster NATS
																																																																																																																			 - Prod → distributed NATS JetStream

																																																																																																																			 **docker/nats.yaml**
																																																																																																																			 ```yaml
																																																																																																																			 version: "3.8"
																																																																																																																			 services:
																																																																																																																			 	nats:
																																																																																																																						image: nats:latest
																																																																																																																								command: "-js -m 8222"
																																																																																																																										ports:
																																																																																																																													- "4222:4222"
																																																																																																																																- "8222:8222"
																																																																																																																																```

																																																																																																																																### FASE 4 — GOVERNANCE LAYER (IMOB DIGITAL CORE)
																																																																																																																																- 6 USERS SYSTEM (OBRIGATÓRIO): ADMIN_MASTER, BROKER, CLIENT, OWNER, INVESTOR, SYSTEM (JOHN AI)
																																																																																																																																- Permission Matrix (RBAC CORE): definir ações permitidas por papel

																																																																																																																																### FASE 5 — IMOB DIGITAL CONTRACT ENGINE
																																																																																																																																- Nenhuma venda existe sem contrato gerado pelo CORE-DNA
																																																																																																																																- Eventos: contract.created, contract.signed, contract.locked, commission.protected, deal.closed, bypass.detected

																																																																																																																																**Contract Schema:**
																																																																																																																																```python
																																																																																																																																@dataclass
																																																																																																																																class Contract:
																																																																																																																																		id: str
																																																																																																																																				property_id: str
																																																																																																																																						parties: list
																																																																																																																																								value: float
																																																																																																																																										status: str  # draft/signed/locked
																																																																																																																																												hash: str
																																																																																																																																												```

																																																																																																																																												### FASE 6 — JOHN + CEFEIDA INTEGRATION LAYER
																																																																																																																																												- John NÃO executa lógica, só interpreta eventos
																																																																																																																																												- CEFEIDA só calcula (FP puro)
																																																																																																																																												- Fluxo: EVENT → CEFEIDA (FP) → SDK → JOHN → SCRIPT DE VENDA → EVENT UPDATE

																																																																																																																																												### FASE 7 — ARCHIMEDES PLUG-IN SYSTEM
																																																																																																																																												- Archimedes NÃO contém lógica própria, apenas consome SDK, EVENTS, CORE-DNA

																																																																																																																																												### FASE 8 — TEST STRATEGY (OBRIGATÓRIO)
																																																																																																																																												- brain_lib → 100% pure function test
																																																																																																																																												- stream_bus → event delivery test
																																																																																																																																												- sdk → integration test
																																																																																																																																												- governance → RBAC test
																																																																																																																																												- contracts → legal flow test

																																																																																																																																												### FASE 9 — CI/CD (GITHUB ACTIONS)
																																																																																																																																												**Pipeline obrigatório:**
																																																																																																																																												```yaml
																																																																																																																																												name: LICEU 6.0 CORE BUILD
																																																																																																																																												on: [push]
																																																																																																																																												jobs:
																																																																																																																																													build:
																																																																																																																																															runs-on: ubuntu-latest
																																																																																																																																																	steps:
																																																																																																																																																				- checkout
																																																																																																																																																							- setup python
																																																																																																																																																										- install dependencies
																																																																																																																																																													- compile protobuf
																																																																																																																																																																- run tests
																																																																																																																																																																			- build sdk
																																																																																																																																																																			```

																																																																																																																																																																			### FASE 10 — NEXT LEVEL (EVOLUÇÃO DO SISTEMA)
																																																																																																																																																																			- Pronto para expansão, versionamento e integração contínua.

																																																																																																																																																																			---
# First Flow Runbook

## Scenario
- New business: Empreendimento 20 casas
- Full lifecycle: governance -> approval -> orchestration -> execution -> audit -> hospital -> academy -> finance -> business case

## Option 1: One-shot API playbook
From backend folder, with API already running:

```bash
./scripts/demo_first_flow.sh
```

VS Code one-click task:

1. Run `Terminal: Run Task`
2. Select `CV Backend: Demo First Flow`

Optional environment variables:

```bash
API_BASE=http://localhost:8000
USER_NAME=irmandade_demo
USER_PASS=demo123
PORTAL=workspace
./scripts/demo_first_flow.sh
```

## Option 2: Manual API flow
1. Login:
```bash
curl -X POST "$API_BASE/auth/sso/login" -H "Content-Type: application/json" -d '{"username":"irmandade_demo","password":"demo123","portal":"workspace"}'
```

2. Create business pipeline:
```bash
curl -X POST "$API_BASE/business-pipeline" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Empreendimento 20 casas","portfolio":"Obras Comuns","program":"Residencial","stage":"Ideia","estimated_cost":2000000,"expected_return":3200000}'
```

3. Approve stage:
```bash
curl -X PATCH "$API_BASE/business-pipeline/$PIPELINE_ID" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"stage":"Aprovado"}'
```

4. Fetch runtime:
```bash
curl -X GET "$API_BASE/business-pipeline/$PIPELINE_ID/runtime" -H "Authorization: Bearer $TOKEN"
```

5. Simulate execution error:
```bash
curl -X POST "$API_BASE/projects/$PROJECT_ID/tasks/complete" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"task":"fundação","has_error":true,"error_description":"Falha em campo","assigned_to":"obra.team.alpha"}'
```

6. Realize financials:
```bash
curl -X POST "$API_BASE/projects/$PROJECT_ID/finance/realize" -H "Authorization: Bearer $TOKEN"
```

7. Close business and create business case:
```bash
curl -X POST "$API_BASE/business-pipeline/$PIPELINE_ID/close" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"lessons_learned":"Fluxo concluido","duration":18,"success":true}'
```

8. Inspect timeline:
```bash
curl -X GET "$API_BASE/business-pipeline/$PIPELINE_ID/timeline?hours=24&limit=200&offset=0" -H "Authorization: Bearer $TOKEN"
```

## Expected key events
- business.created
- business.approved
- project.created
- execution.started
- task.completed
- audit.detected
- training.required
- process.updated
- financial.updated
- business.closed

## Governance and RBAC baseline

### Canonical roles
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

### Organizational hierarchy and monolith scope
- SUPER_ADMIN (John Monolito): sees all monoliths, approves John IA decisions, creates strategies, releases capital.
	Monoliths: LICEU CORE + all.
- DIRETOR ESTRATEGICO: sees portfolio, macro indicators and simulations, approves projects and priorities.
	Monoliths: LICEU + ECONOTECH + CEFEIDA.
- DIRETOR FINANCEIRO: sees DRE, cash flow and investments, releases payments and adjusts budgets.
	Monoliths: HUB + CEA.
- DIRETOR DE ENGENHARIA: sees all works, schedules and performance, drives technical decisions and resource redistribution.
	Monoliths: OPERA + BIM/ENG.
- DIRETOR DE QUALIDADE (P&D): sees processes, audits and non-conformities, changes processes and defines standards.
	Monoliths: P&D + ANCHOR.
- AUDITOR / HOSPITAL: sees enterprise health, risks and failures, opens interventions and can block operation.
	Monoliths: AUDIT + HOSPITAL.
- GERENTE DE PROJETO: sees one project, team and tasks, executes project and reports progress.
	Monoliths: OPERA.
- FORNECEDOR: sees orders, contracts and demand, updates supply capacity and delivery.
	Monoliths: FORNECEDORES.
- CLIENTE: sees own project, status and documents, follows and approves milestones.
	Monoliths: ARCHIMEDES / OPERA.
- COLABORADOR / APRENDIZ: sees trainings and assigned tasks, executes activities and learns processes.
	Monoliths: ACADEMIA + OPERA.

### Simplified action matrix
- approve strategy: SUPER_ADMIN + DIRETOR
- release payment: FINANCEIRO
- execute work: GERENTE
- change process: QUALIDADE
- see everything: SUPER_ADMIN

### API governance endpoints
- GET /governance/roles
- POST /governance/approve-strategy
- POST /governance/release-payment
- POST /governance/execute-work
- POST /governance/change-process
- POST /governance/approve-john

### Core rule
- Higher power means fewer users.

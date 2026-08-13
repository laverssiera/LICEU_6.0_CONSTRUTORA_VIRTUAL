# Checklist de Producao - LICEU 6.0 Core

## 1) Banco e Migracoes (Alembic)

- [ ] Garantir `DATABASE_URL` de producao no ambiente.
- [ ] Garantir dependencias instaladas:
  - `pip install -r requirements.txt`
- [ ] Confirmar estrutura Alembic presente no backend:
  - `alembic.ini`
  - `alembic/env.py`
  - `alembic/versions/20260430_0001_enterprise_unified_schema.py`
  - `alembic/versions/20260430_0002_enterprise_domain_constraints.py`
- [ ] Aplicar migrations em staging/producao:
  - `cd cv-backend-core && ./scripts/staging_enterprise_rollout.sh`
  - preflight sem alterar banco: `cd cv-backend-core && ./scripts/staging_enterprise_rollout.sh --dry-run`
  - preflight bloqueante: `cd cv-backend-core && ./scripts/staging_enterprise_rollout.sh --dry-run --strict-preflight`
  - o script roda migration, seeds e sanity SQL automaticamente
  - evidencias: salvar output da execucao e resultado das queries
  - runbook: `ENTERPRISE_STAGING_RUNBOOK.md`
  - sanity SQL: `scripts/post_migration_sanity.sql`
  - fallback local: `cd cv-backend-core && ./scripts/bootstrap_enterprise.sh`
  - (alternativo) `cd cv-backend-core && $(python -c "import sysconfig; print(sysconfig.get_path('scripts') + '/alembic')") -c alembic.ini upgrade head`
- [ ] Validar query basica nas tabelas criticas.

## 2) Seed RBAC (6 perfis obrigatorios)

- [ ] Executar seed de RBAC legado (orquestracao):
  - `python scripts/seed_rbac.py`
- [ ] Executar seed enterprise bootstrap (core + IAM):
  - `python scripts/seed_enterprise_bootstrap.py`
- [ ] Confirmar perfis criados:
  - `ADMIN_MASTER`, `BROKER`, `CLIENT`, `OWNER`, `INVESTOR`, `SYSTEM`
- [ ] Confirmar matriz de permissao em `role_permissions`.

## 3) Event Backbone e Registry

- [ ] Subir NATS/JetStream no ambiente.
- [ ] Validar publicacao e consumo dos eventos:
  - `work.created`
  - `work.updated`
  - `work.assigned`
  - `decision.made`
- [ ] Confirmar versionamento no registry (`*.v1`, `*.v2` quando aplicavel).

## 4) API Core e Realtime

- [ ] Validar endpoints:
  - `POST /work`
  - `GET /work`
  - `PATCH /work/{id}`
  - `POST /work/{id}/orchestrate`
  - `POST /events`
  - `GET /events`
  - `POST /plugins/monolith/register`
- [ ] Validar websocket:
  - `WS /ws/work/updates`

## 5) Observabilidade

- [ ] Habilitar logs estruturados por ambiente.
- [ ] Incluir correlation id por requisicao e por evento.
- [ ] Coletar metricas minimas:
  - throughput de work/s
  - latencia de orquestracao
  - taxa de erro por endpoint
  - backlog de eventos
- [ ] Integrar alertas para:
  - falha de heartbeat monolith_registry
  - erro continuo de publicacao de eventos
  - aumento de 5xx

## 6) Hardening de Seguranca

- [ ] Revisar segredos e rotacionar chaves JWT/SSO.
- [ ] Forcar HTTPS no ingress.
- [ ] Aplicar limite de taxa em endpoints criticos.
- [ ] Revisar escopos de acesso para orquestracao segura.
- [ ] Revisar politica anti-bypass e trilha de auditoria.

## 7) Qualidade e Release

- [ ] Rodar suite completa:
  - `pytest -q`
- [ ] Executar smoke test de orquestracao fim a fim.
- [ ] Publicar release notes com breaking changes.
- [ ] Definir plano de rollback (DB + API + event contracts).

## Artefatos entregues junto do checklist

- Seed RBAC utilitario: `app/services/rbac_seed.py`
- Executor de seed: `scripts/seed_rbac.py`
- Seed bootstrap enterprise: `scripts/seed_enterprise_bootstrap.py`
- Script de rollout staging: `scripts/staging_enterprise_rollout.sh`
- Sanity checks SQL: `scripts/post_migration_sanity.sql`
- Runbook staging enterprise: `ENTERPRISE_STAGING_RUNBOOK.md`
- Runbook do primeiro fluxo (manual + playbook): `FIRST_FLOW_RUNBOOK.md`
- Schema enterprise unificado: `sql/enterprise_unified_schema.sql`
- Revisoes Alembic enterprise: `alembic/versions/20260430_0001_enterprise_unified_schema.py`, `alembic/versions/20260430_0002_enterprise_domain_constraints.py`
- Modelos DB core: `app/models/orchestration.py`
- Runtime core: `app/services/orchestration_runtime.py`

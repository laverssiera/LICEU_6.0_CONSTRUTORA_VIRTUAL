# Enterprise Staging Runbook

## Objective
Apply enterprise migrations + seeds on staging and validate production-critical integrity immediately after rollout.

## Preconditions
- `DATABASE_URL` points to staging PostgreSQL.
- Python dependencies installed (`pip install -r ../requirements.txt`).
- Alembic installed (`python -m pip install alembic`) if not already in environment.
- PostgreSQL client available (`psql`).

## One-command rollout
From backend root:

```bash
./scripts/staging_enterprise_rollout.sh
```

## Dry-run (no changes)
To validate prerequisites and print the execution plan without applying changes:

```bash
./scripts/staging_enterprise_rollout.sh --dry-run
```

To make preflight checks blocking even in dry-run mode:

```bash
./scripts/staging_enterprise_rollout.sh --dry-run --strict-preflight
```

## Manual fallback steps
```bash
cd cv-backend-core
$(python -c "import sysconfig; print(sysconfig.get_path('scripts') + '/alembic')") -c alembic.ini upgrade head
python scripts/seed_rbac.py
python scripts/seed_enterprise_bootstrap.py
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/post_migration_sanity.sql
```

## Go/No-Go checks
- `alembic_version` must be `20260430_0002`.
- Required tables must exist (core, IAM, audit, security).
- Required indexes must exist: `idx_org`, `idx_user_org`, `idx_events_type`.
- Domain constraints from revision 0002 must exist.
- Integrity counters should be zero:
  - `users_without_org`
  - `tenant_access_without_user`
  - `tenant_access_without_tenant`

## Rollback guideline
If rollout fails after migration start:
1. Freeze writes to backend APIs.
2. Inspect failing migration and DB state.
3. If safe and approved, run:
   ```bash
   $(python -c "import sysconfig; print(sysconfig.get_path('scripts') + '/alembic')") -c alembic.ini downgrade 20260430_0001
   ```
4. Re-run sanity checks and document incident.

## Evidence to store
- Command output logs from rollout script.
- Sanity query outputs.
- Timestamp and operator name.

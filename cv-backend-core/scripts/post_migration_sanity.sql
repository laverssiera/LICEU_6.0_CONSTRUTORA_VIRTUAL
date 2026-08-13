-- Enterprise sanity checks after Alembic + seeds
-- Usage example:
-- psql "$DATABASE_URL" -f scripts/post_migration_sanity.sql

-- 1) Migration version
SELECT version_num AS alembic_version FROM alembic_version;

-- 2) Critical table existence
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'organizations',
    'users',
    'roles',
    'permissions',
    'role_permissions',
    'events',
    'audit_events',
    'company_health',
    'security_logs'
  )
ORDER BY table_name;

-- 3) Core bootstrap records
SELECT COUNT(*) AS organizations_count FROM organizations;
SELECT COUNT(*) AS users_count FROM users;
SELECT COUNT(*) AS roles_count FROM roles;
SELECT COUNT(*) AS permissions_count FROM permissions;
SELECT COUNT(*) AS role_permissions_count FROM role_permissions;
SELECT COUNT(*) AS user_roles_count FROM user_roles;

-- 4) Required indexes
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_org', 'idx_user_org', 'idx_events_type')
ORDER BY indexname;

-- 5) Domain constraints created by revision 0002
SELECT conname
FROM pg_constraint
WHERE conname IN (
  'chk_organizations_type',
  'chk_users_status',
  'chk_business_pipeline_risk_level',
  'chk_audit_events_severity',
  'chk_security_logs_severity',
  'chk_tasks_status',
  'chk_tasks_priority',
  'chk_dre_entries_type',
  'chk_company_health_overall_score'
)
ORDER BY conname;

-- 6) Quick integrity checks
SELECT COUNT(*) AS users_without_org
FROM users u
LEFT JOIN organizations o ON o.id = u.organization_id
WHERE o.id IS NULL;

SELECT COUNT(*) AS tenant_access_without_user
FROM tenant_data_access tda
LEFT JOIN users u ON u.id = tda.user_id
WHERE u.id IS NULL;

SELECT COUNT(*) AS tenant_access_without_tenant
FROM tenant_data_access tda
LEFT JOIN tenants t ON t.id = tda.tenant_id
WHERE t.id IS NULL;

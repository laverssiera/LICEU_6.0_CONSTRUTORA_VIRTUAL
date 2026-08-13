"""
Cognitive DB Core
Camada central de orquestração de bancos de dados do LICEU 6.0
"""

class CognitiveDB:
    def __init__(self):
        self.tenants = {}
        self.databases = {}
        self.status = {}

    def register_tenant(self, tenant_id, config):
        self.tenants[tenant_id] = config

    def add_database(self, tenant_id, db_info):
        self.databases.setdefault(tenant_id, []).append(db_info)

    def get_status(self):
        return {
            "tenants": list(self.tenants.keys()),
            "databases": self.databases,
            "status": self.status
        }

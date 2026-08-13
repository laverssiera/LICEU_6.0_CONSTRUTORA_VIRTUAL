"""
Exemplo de uso do LICEU DATA FABRIC
"""
from fabric_core import DatabaseFabricCore

def main():
    fabric = DatabaseFabricCore()
    # Cadastro de tenant
    fabric.register_tenant("tenant_1", {"name": "Construtora Alpha", "contact": "alpha@liceu.com"})
    # Adiciona banco para o tenant
    fabric.add_database("tenant_1", {"db_id": "db_alpha", "type": "postgres", "status": "active"})
    # Adiciona réplica
    fabric.add_replica("db_alpha", {"replica_id": "replica1", "location": "us-east", "status": "ok"})
    # Consulta status
    status = fabric.get_status()
    print("Status do Data Fabric:", status)

if __name__ == "__main__":
    main()

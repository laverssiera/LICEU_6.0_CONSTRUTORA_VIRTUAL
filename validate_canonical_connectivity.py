#!/usr/bin/env python3
"""
CANONICAL_DATABASE_CONNECTIVITY Gate Validator
Valida conectividade de rede entre monólitos e Canonical Event Store (db_core_os)

Etapas de validação:
1. Resolução DNS de db_core_os
2. Conectividade TCP ao host:port
3. Conexão PostgreSQL
4. Leitura do banco liceu_core_os na schema public
5. Verificação de public.events
6. Recuperação de eventos específicos (evt-archimedes-001, economic-impact-8823098e873caa50e378325c9)
"""

import sys
import os
import socket
import subprocess
import json
from typing import Dict, Any, Tuple, Optional

# PostgreSQL library
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


class CanonicalConnectivityValidator:
    """Validador de conectividade do Canonical Event Store"""

    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "db_core_os")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "liceu_core_os")
        self.db_user = os.getenv("DB_USER", "admin")
        self.db_password = os.getenv("DB_PASSWORD", "password123")
        self.db_schema = "public"
        
        self.results = {
            "gate": "CANONICAL_DATABASE_CONNECTIVITY",
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "schema": self.db_schema,
            "dns_resolution_valid": False,
            "tcp_connection_valid": False,
            "postgres_connection_valid": False,
            "canonical_read_valid": False,
            "canonical_event_table": "public.events",
            "canonical_repository_valid": False,
            "registry_valid": False,
            "audit_valid": False,
            "lineage_fields_supported": False,
            "w89_event_visible": False,
            "w91_event_visible": False,
            "status": "PENDING",
            "errors": []
        }

    def validate_dns_resolution(self) -> bool:
        """Etapa 1: Valida resolução DNS"""
        print("\n[1/6] Validando resolução DNS para db_core_os...")
        try:
            ip_address = socket.gethostbyname(self.db_host)
            print(f"    ✓ DNS resolution OK: {self.db_host} -> {ip_address}")
            self.results["dns_resolution_valid"] = True
            return True
        except socket.gaierror as e:
            error_msg = f"DNS resolution FAILED: {self.db_host} não resolveu. Erro: {str(e)}"
            print(f"    ✗ {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def validate_tcp_connection(self) -> bool:
        """Etapa 2: Valida conectividade TCP"""
        print(f"\n[2/6] Validando conexão TCP ao {self.db_host}:{self.db_port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.db_host, self.db_port))
            sock.close()
            
            if result == 0:
                print(f"    ✓ TCP connection OK: {self.db_host}:{self.db_port}")
                self.results["tcp_connection_valid"] = True
                return True
            else:
                error_msg = f"TCP connection FAILED: Porta {self.db_port} não respondeu"
                print(f"    ✗ {error_msg}")
                self.results["errors"].append(error_msg)
                return False
        except Exception as e:
            error_msg = f"TCP connection ERROR: {str(e)}"
            print(f"    ✗ {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def validate_postgres_connection(self) -> bool:
        """Etapa 3: Valida conexão PostgreSQL"""
        print(f"\n[3/6] Validando conexão PostgreSQL ({self.db_user}@{self.db_host}/{self.db_name})...")
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0] == 1:
                print(f"    ✓ PostgreSQL connection OK")
                self.results["postgres_connection_valid"] = True
                return conn
            else:
                error_msg = "PostgreSQL connection FAILED: SELECT 1 retornou resultado inesperado"
                print(f"    ✗ {error_msg}")
                self.results["errors"].append(error_msg)
                conn.close()
                return None
                
        except psycopg2.OperationalError as e:
            error_msg = f"PostgreSQL connection FAILED: {str(e)}"
            print(f"    ✗ {error_msg}")
            self.results["errors"].append(error_msg)
            return None
        except Exception as e:
            error_msg = f"PostgreSQL connection ERROR: {str(e)}"
            print(f"    ✗ {error_msg}")
            self.results["errors"].append(error_msg)
            return None

    def validate_canonical_read(self, conn) -> bool:
        """Etapa 4-5: Valida leitura de dados canônicos"""
        if not conn:
            return False

        print(f"\n[4/6] Validando leitura de public.events na schema {self.db_schema}...")
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Verificar se a tabela existe
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'events'
                )
            """, (self.db_schema,))
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                error_msg = f"Tabela events não existe em {self.db_schema}"
                print(f"    ✗ {error_msg}")
                self.results["errors"].append(error_msg)
                cursor.close()
                return False

            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {self.db_schema}.events")
            count = cursor.fetchone()[0]
            print(f"    ✓ public.events encontrada: {count} registros")
            self.results["canonical_read_valid"] = True
            self.results["canonical_repository_valid"] = True

            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'event_registry'
                )
            """, (self.db_schema,))
            self.results["registry_valid"] = bool(cursor.fetchone()[0])

            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'audit_events'
                )
            """, (self.db_schema,))
            self.results["audit_valid"] = bool(cursor.fetchone()[0])

            cursor.execute(f"""
                SELECT payload
                FROM {self.db_schema}.events
                ORDER BY created_at DESC
                LIMIT 50
            """)
            contract_fields = {
                "event_id",
                "source_event_id",
                "trace_id",
                "parent_event_id",
                "causation_id",
                "decision_id",
                "governance_decision_id",
                "execution_id",
                "artifact_id",
                "event_type",
                "scope",
                "producer",
                "contract_id",
                "contract_version",
                "timestamp",
                "payload",
            }
            observed_fields = set()
            for row in cursor.fetchall():
                if isinstance(row["payload"], dict):
                    observed_fields.update(row["payload"].keys())
            self.results["lineage_fields_supported"] = contract_fields.issubset(observed_fields) or count == 0

            # Etapa 5: Procurar por eventos específicos
            print(f"\n[5/6] Procurando por eventos W89 (ARCHIMEDES) e W91 (ECONOMIC)...")
            
            # Buscar evento evt-archimedes-001
            cursor.execute(f"""
                SELECT id, event_type, payload, created_at 
                FROM {self.db_schema}.events 
                WHERE id = %s OR event_type ILIKE %s OR payload::text ILIKE %s
                LIMIT 1
            """, ('evt-archimedes-001', '%archimedes%', '%evt-archimedes-001%'))
            
            w89_result = cursor.fetchone()
            if w89_result:
                print(f"    ✓ W89 Event (ARCHIMEDES) encontrado: {w89_result['id']}")
                self.results["w89_event_visible"] = True
            else:
                print(f"    ⚠ W89 Event (evt-archimedes-001) não encontrado (pode estar OK se ainda não foi publicado)")
                self.results["w89_event_visible"] = False

            # Buscar evento economic-impact
            cursor.execute(f"""
                SELECT id, event_type, payload, created_at 
                FROM {self.db_schema}.events 
                WHERE id LIKE %s OR event_type ILIKE %s OR payload::text ILIKE %s
                LIMIT 1
            """, ('%economic-impact%', '%economic%', '%economic-impact%'))
            
            w91_result = cursor.fetchone()
            if w91_result:
                print(f"    ✓ W91 Event (ECONOMIC) encontrado: {w91_result['id']}")
                self.results["w91_event_visible"] = True
            else:
                print(f"    ⚠ W91 Event (economic-impact-*) não encontrado (pode estar OK se ainda não foi publicado)")
                self.results["w91_event_visible"] = False

            cursor.close()
            return True

        except Exception as e:
            error_msg = f"Canonical read ERROR: {str(e)}"
            print(f"    ✗ {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def validate_docker_network(self) -> bool:
        """Valida configuração da rede Docker"""
        print(f"\n[6/6] Validando configuração da rede Docker (liceu-net)...")
        try:
            # Tentar obter informações da rede usando docker CLI
            result = subprocess.run(
                ["docker", "network", "inspect", "liceu-net"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                warning_msg = f"Docker network 'liceu-net' não encontrada ou acessível via CLI"
                print(f"    ⚠ {warning_msg} (pode ser esperado se executando fora do Docker)")
                return True
            
            try:
                network_info = json.loads(result.stdout)
                print(f"    ✓ Docker network 'liceu-net' encontrada")
                
                # Verificar se db_core_os está na rede
                containers = network_info[0].get('Containers', {})
                db_core_os_found = any(
                    'db_core_os' in container.get('Name', '')
                    for container in containers.values()
                    if isinstance(container, dict)
                )
                
                if db_core_os_found:
                    print(f"    ✓ Container db_core_os está na rede liceu-net")
                else:
                    print(f"    ⚠ Container db_core_os não encontrado na rede (pode estar parado)")
                
                return True
            except json.JSONDecodeError:
                print(f"    ⚠ Não foi possível parsear resposta do Docker (formato JSON inválido)")
                return True
                
        except subprocess.TimeoutExpired:
            print(f"    ⚠ Timeout ao executar docker network inspect")
            return True
        except FileNotFoundError:
            print(f"    ⚠ Docker CLI não disponível (executando fora do Docker ou Docker não instalado)")
            return True
        except Exception as e:
            print(f"    ⚠ Erro ao validar rede Docker: {str(e)}")
            return True

    def validate(self) -> Dict[str, Any]:
        """Executa todas as validações"""
        print("=" * 70)
        print("CANONICAL_DATABASE_CONNECTIVITY Validator")
        print("=" * 70)
        print(f"Alvo: {self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}")
        
        # Executar validações
        if not self.validate_dns_resolution():
            self.results["status"] = "BLOCKED"
            print("\n❌ BLOQUEADO: DNS resolution falhou")
            return self.results

        if not self.validate_tcp_connection():
            self.results["status"] = "BLOCKED"
            print("\n❌ BLOQUEADO: TCP connection falhou")
            return self.results

        conn = self.validate_postgres_connection()
        if not conn:
            self.results["status"] = "BLOCKED"
            print("\n❌ BLOQUEADO: PostgreSQL connection falhou")
            return self.results

        if not self.validate_canonical_read(conn):
            self.results["status"] = "BLOCKED"
            print("\n❌ BLOQUEADO: Canonical read falhou")
            return self.results

        self.validate_docker_network()

        # Determinar status final
        if self.results["dns_resolution_valid"] and \
           self.results["tcp_connection_valid"] and \
           self.results["postgres_connection_valid"] and \
           self.results["canonical_read_valid"]:
            self.results["status"] = "PASS"
            print("\n✅ PASSOU: Conectividade canônica validada com sucesso!")
        else:
            self.results["status"] = "FAILED"
            print("\n❌ FALHOU: Uma ou mais validações falharam")

        return self.results

    def print_results(self):
        """Imprime resultados formatados"""
        print("\n" + "=" * 70)
        print("RESULTADO DA VALIDAÇÃO")
        print("=" * 70)
        print(json.dumps(self.results, indent=2))
        print("=" * 70)


def main():
    validator = CanonicalConnectivityValidator()
    results = validator.validate()
    validator.print_results()
    
    # Salvar resultados em arquivo JSON
    output_file = "CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResultados salvos em: {output_file}")
    
    # Retornar código de saída apropriado
    sys.exit(0 if results["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()

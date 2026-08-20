#!/usr/bin/env python3
"""
CANONICAL_DATABASE_CONNECTIVITY - Remediation Script
Corrige automaticamente problemas de conectividade detectados

Funciona por:
1. Verificar docker-compose.yml
2. Garantir rede liceu-net
3. Adicionar consumidores à rede se faltando
4. Regenerar containers com nova configuração
5. Validar conectividade
"""

import sys
import os
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class CanonicalConnectivityRemediation:
    """Remediador de conectividade canônica"""

    def __init__(self, docker_compose_path: str = "docker-compose.yml"):
        self.docker_compose_path = Path(docker_compose_path)
        self.compose_data = None
        self.backups = []
        
        if not self.docker_compose_path.exists():
            raise FileNotFoundError(f"docker-compose.yml não encontrado: {self.docker_compose_path}")

    def load_compose(self) -> Dict:
        """Carrega arquivo docker-compose"""
        try:
            with open(self.docker_compose_path, 'r') as f:
                self.compose_data = yaml.safe_load(f)
            print(f"✓ docker-compose.yml carregado: {self.docker_compose_path}")
            return self.compose_data
        except Exception as e:
            print(f"✗ Erro ao carregar docker-compose.yml: {str(e)}")
            raise

    def save_compose(self):
        """Salva arquivo docker-compose com backup"""
        if self.compose_data is None:
            raise RuntimeError("Nenhum dado para salvar")

        # Criar backup
        backup_path = self.docker_compose_path.with_suffix('.yml.bak')
        import shutil
        shutil.copy(self.docker_compose_path, backup_path)
        self.backups.append(backup_path)
        print(f"✓ Backup criado: {backup_path}")

        # Salvar arquivo
        try:
            with open(self.docker_compose_path, 'w') as f:
                yaml.dump(self.compose_data, f, default_flow_style=False, sort_keys=False)
            print(f"✓ docker-compose.yml salvo")
        except Exception as e:
            print(f"✗ Erro ao salvar docker-compose.yml: {str(e)}")
            raise

    def ensure_network_exists(self) -> bool:
        """Garante que rede liceu-net existe e está configurada"""
        print("\n[REMEDIAÇÃO 1/5] Garantindo rede liceu-net...")
        
        if 'networks' not in self.compose_data:
            self.compose_data['networks'] = {}
        
        if 'liceu-net' not in self.compose_data['networks']:
            self.compose_data['networks']['liceu-net'] = {
                'name': 'liceu-net',
                'driver': 'bridge'
            }
            print("  ✓ Rede liceu-net adicionada ao docker-compose")
            return True
        else:
            net_config = self.compose_data['networks']['liceu-net']
            if isinstance(net_config, dict) and net_config.get('driver') == 'bridge':
                print("  ✓ Rede liceu-net já existe e está configurada corretamente")
                return False
            else:
                net_config['name'] = 'liceu-net'
                net_config['driver'] = 'bridge'
                print("  ✓ Rede liceu-net atualizada")
                return True

    def ensure_db_core_os_in_network(self) -> bool:
        """Garante que db_core_os está na rede liceu-net"""
        print("\n[REMEDIAÇÃO 2/5] Garantindo db_core_os na rede liceu-net...")
        
        if 'services' not in self.compose_data:
            self.compose_data['services'] = {}
        
        if 'db_core_os' not in self.compose_data['services']:
            print("  ✗ Serviço db_core_os não encontrado!")
            return False
        
        db_service = self.compose_data['services']['db_core_os']
        
        if 'networks' not in db_service:
            db_service['networks'] = []
        
        # Converter para lista se for string
        if isinstance(db_service['networks'], str):
            db_service['networks'] = [db_service['networks']]
        elif not isinstance(db_service['networks'], list):
            db_service['networks'] = []
        
        if 'liceu-net' not in db_service['networks']:
            db_service['networks'].append('liceu-net')
            print("  ✓ db_core_os adicionado à rede liceu-net")
            return True
        else:
            print("  ✓ db_core_os já está na rede liceu-net")
            return False

    def add_consumers_to_network(self) -> bool:
        """Adiciona consumidores do backbone à rede liceu-net"""
        print("\n[REMEDIAÇÃO 3/5] Adicionando consumidores à rede liceu-net...")
        
        # Lista de serviços que DEVEM acessar db_core_os
        consumer_services = [
            'backend',
            'john-crm',
            'john-engine',
            'cea-investimentos-api',
            'econo-tech-api',
            'erp-fornecedores-api',
            'bim-arqu-eng-api',
            'archimedes-api',
            'hub-contabil-api',
            'cefeida-api',
            'pdi-ia-api',
            'cdvirtual-api',
            'invest-tech-api',
            'academia-saber-api',
            'gtamkt-api',
            'juridicotech-api',
            'joh-brasileiro-api',
            'gateway',
            'api',
            'app'
        ]
        
        services = self.compose_data.get('services', {})
        modified = False
        
        for service_name, service_config in services.items():
            # Verificar se é um serviço consumidor (por nome)
            is_consumer = any(
                consumer in service_name.lower() 
                for consumer in consumer_services
            )
            
            # Também considerar serviços que dependem de db_core_os
            depends_on = service_config.get('depends_on', {})
            if isinstance(depends_on, list):
                depends_on = {s: {} for s in depends_on}
            
            is_dependent = 'db_core_os' in depends_on
            
            if is_consumer or is_dependent:
                if 'networks' not in service_config:
                    service_config['networks'] = []
                
                # Converter para lista se necessário
                if isinstance(service_config['networks'], str):
                    service_config['networks'] = [service_config['networks']]
                elif not isinstance(service_config['networks'], list):
                    service_config['networks'] = []
                
                if 'liceu-net' not in service_config['networks']:
                    service_config['networks'].append('liceu-net')
                    print(f"  ✓ {service_name} adicionado à rede liceu-net")
                    modified = True
        
        return modified

    def ensure_healthcheck(self) -> bool:
        """Garante que db_core_os tem healthcheck configurado"""
        print("\n[REMEDIAÇÃO 4/5] Garantindo healthcheck para db_core_os...")
        
        db_service = self.compose_data['services'].get('db_core_os', {})
        
        if 'healthcheck' not in db_service:
            db_service['healthcheck'] = {
                'test': ['CMD-SHELL', 'pg_isready -U admin -d liceu_core_os'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
            print("  ✓ Healthcheck adicionado ao db_core_os")
            return True
        else:
            print("  ✓ Healthcheck já está configurado")
            return False

    def validate_credentials(self) -> bool:
        """Valida credenciais de db_core_os"""
        print("\n[REMEDIAÇÃO 5/5] Validando credenciais...")
        
        db_service = self.compose_data['services'].get('db_core_os', {})
        env = db_service.get('environment', {})
        
        required_vars = {
            'POSTGRES_DB': 'liceu_core_os',
            'POSTGRES_USER': 'admin',
            'POSTGRES_PASSWORD': 'password123'
        }
        
        all_valid = True
        for var_name, expected_value in required_vars.items():
            actual_value = env.get(var_name)
            if actual_value == expected_value:
                print(f"  ✓ {var_name}: {actual_value}")
            else:
                print(f"  ⚠ {var_name}: {actual_value} (esperado: {expected_value})")
                env[var_name] = expected_value
                all_valid = False
        
        return not all_valid

    def regenerate_docker_compose(self) -> bool:
        """Regenera docker-compose com todas as correções"""
        print("\n[REMEDIAÇÃO FINAL] Regenerando docker-compose.yml...")
        
        changes_made = False
        changes_made |= self.ensure_network_exists()
        changes_made |= self.ensure_db_core_os_in_network()
        changes_made |= self.add_consumers_to_network()
        changes_made |= self.ensure_healthcheck()
        changes_made |= self.validate_credentials()
        
        if changes_made:
            self.save_compose()
            print("  ✓ docker-compose.yml atualizado com sucesso")
            return True
        else:
            print("  ✓ Nenhuma alteração necessária")
            return False

    def docker_compose_up(self, force: bool = False) -> bool:
        """Reinicia docker-compose"""
        print("\n[RESTART] Reiniciando docker-compose...")
        
        try:
            print("  • Parando serviços...")
            subprocess.run(['docker-compose', 'down'], check=True, cwd=self.docker_compose_path.parent)
            
            print("  • Iniciando serviços...")
            subprocess.run(['docker-compose', 'up', '-d'], check=True, cwd=self.docker_compose_path.parent)
            
            print("  ✓ docker-compose reiniciado")
            
            # Aguardar healthchecks
            print("  • Aguardando healthchecks...")
            for i in range(30):
                result = subprocess.run(
                    ['docker', 'ps', '--filter', 'name=db_core_os', '--format', '{{.Status}}'],
                    capture_output=True,
                    text=True
                )
                if 'healthy' in result.stdout:
                    print(f"    ✓ db_core_os healthy")
                    return True
                print(f"    Aguardando... ({i+1}/30)")
                import time
                time.sleep(2)
            
            print("  ⚠ Timeout aguardando healthcheck")
            return False
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Erro: {str(e)}")
            return False

    def remediate(self, restart: bool = True) -> bool:
        """Executa remediação completa"""
        print("=" * 70)
        print("CANONICAL_DATABASE_CONNECTIVITY - REMEDIATION")
        print("=" * 70)
        
        try:
            self.load_compose()
            changes = self.regenerate_docker_compose()
            
            if restart and changes:
                return self.docker_compose_up()
            
            return True
        except Exception as e:
            print(f"\n✗ Erro na remediação: {str(e)}")
            
            # Restaurar backups
            if self.backups:
                print(f"\nRestaurando backups...")
                for backup in self.backups:
                    import shutil
                    original = backup.with_suffix('')
                    shutil.copy(backup, original)
                    print(f"  ✓ Restaurado: {original}")
            
            return False


def main():
    docker_compose_path = Path.cwd() / "docker-compose.yml"
    
    if not docker_compose_path.exists():
        print(f"✗ docker-compose.yml não encontrado em {docker_compose_path}")
        sys.exit(1)
    
    try:
        remediation = CanonicalConnectivityRemediation(str(docker_compose_path))
        
        # Perguntar se deseja fazer restart
        print("\nDeseja reiniciar docker-compose após remediação? (s/n) [s]: ", end="", flush=True)
        try:
            # Tentar ler stdin; se não disponível, assume 's'
            response = input().lower().strip()
        except:
            response = 's'
        
        restart = response != 'n'
        
        success = remediation.remediate(restart=restart)
        
        print("\n" + "=" * 70)
        if success:
            print("✅ REMEDIAÇÃO CONCLUÍDA COM SUCESSO")
            print("=" * 70)
            print("\nPróximos passos:")
            print("  1. Executar validação: python3 validate_canonical_connectivity.py")
            print("  2. Verificar logs: docker logs db_core_os")
            print("  3. Testar acesso de cada monólito")
            sys.exit(0)
        else:
            print("❌ REMEDIAÇÃO FALHOU")
            print("=" * 70)
            print("\nConsulte os logs acima para detalhes.")
            sys.exit(1)
    
    except Exception as e:
        print(f"✗ Erro inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Verificar se PyYAML está instalado
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
        sys.exit(1)
    
    main()

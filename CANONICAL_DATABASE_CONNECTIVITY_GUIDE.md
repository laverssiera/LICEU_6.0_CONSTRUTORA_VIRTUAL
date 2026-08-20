# CANONICAL_DATABASE_CONNECTIVITY - Diagnóstico e Remediação

## DIAGNÓSTICO

### Problema Identificado
A WAVE 92 está corretamente configurada para usar `db_core_os:5432/liceu_core_os`, mas há uma desconexão de rede que impede que os monólitos consumidores (CEA, ECONOTECH, FORNECEDORES, BIM ARCH ENG, ARCHIMEDES, OPERA, etc.) acessem o Canonical Event Store.

### Configuração Atual (✓ Correta)
```
Database URL: postgresql://admin:password123@db_core_os:5432/liceu_core_os
Serviço: db_core_os
Container: db_core_os
Porta Exposta: 5542 (Docker) → 5432 (PostgreSQL)
Rede: liceu-net (bridge)
Schema: public
Banco: liceu_core_os
```

### Falha Atual
**db_core_os NÃO resolve no ambiente onde os monólitos estão executando**

Possíveis causas:
1. **Rede Docker**: CEA/Monólitos não estão na rede `liceu-net`
2. **DNS Interno**: Docker DNS não resolvendo `db_core_os`
3. **TCP**: Firewall ou configuração de porta bloqueando acesso
4. **Credenciais**: Usuário/senha mismatch
5. **Execução Fora do Docker**: CEA em host, PostgreSQL em container

---

## CONFIGURAÇÃO DO DOCKER-COMPOSE.yml

### Serviço db_core_os (Linha 235-249)
```yaml
db_core_os:
  <<: *postgres-template  # Herda template com healthcheck
  container_name: db_core_os
  environment:
    POSTGRES_DB: liceu_core_os
    POSTGRES_USER: admin
    POSTGRES_PASSWORD: password123
  ports:
    - "5542:5432"          # Host 5542 → Container 5432
  volumes:
    - db_core_os_data:/var/lib/postgresql/data
```

### Rede Oficial (Linha 424-427)
```yaml
networks:
  liceu-net:
    name: liceu-net
    driver: bridge
```

### Consumidores do Backbone Canônico
Todos DEVEM estar na rede `liceu-net`:
- ✓ `backend` → DATABASE_URL: `db_core_os:5432/liceu_core_os`
- ✓ `john-crm` → depends_on: `db_core_os (service_healthy)`
- ✓ `john-engine` → depends_on: `db_core_os (service_healthy)`
- Demais monólitos (CEA, ECONOTECH, FORNECEDORES, etc.)

---

## 12 ETAPAS DE VALIDAÇÃO

### 1. Localizar docker-compose oficial
```bash
ls -la /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/docker-compose.yml
```
✓ Arquivo confirmado: `/docker-compose.yml`

### 2. Confirmar serviço db_core_os
```bash
grep -A 15 "db_core_os:" docker-compose.yml
```
✓ Serviço definido
✓ container_name: db_core_os
✓ POSTGRES_DB: liceu_core_os
✓ POSTGRES_USER: admin

### 3. Confirmar configurações
- ✓ container_name: `db_core_os`
- ✓ networks: `liceu-net`
- ✓ healthcheck: `pg_isready -U admin -d $$POSTGRES_DB`
- ✓ exposed ports: `5542:5432`

### 4. Identificar rede do CEA
```bash
docker ps --filter "name=cea" --format "table {{.Names}}\t{{.Networks}}"
# Ou verificar docker-compose para CEA/ECONOTECH
```

### 5. Conectar à mesma rede
CEA, ECONOTECH, FORNECEDORES e todos os monólitos DEVEM ter:
```yaml
networks:
  - liceu-net
```

### 6. Garantir DNS interno
Docker DNS automático: `db_core_os` resolve para IP do container
Validar com:
```bash
docker exec <container_consumer> getent hosts db_core_os
# Ou: docker exec <container_consumer> nslookup db_core_os
```

### 7-8. Validar TCP e DNS de dentro do container
```bash
# De dentro de um container na rede liceu-net:
docker exec <container> bash -c "nc -zv db_core_os 5432"
docker exec <container> bash -c "getent hosts db_core_os"
```

### 9. Validar conexão PostgreSQL
```bash
# De dentro do container ou do host:
psql -h db_core_os -U admin -d liceu_core_os -c "SELECT 1"
# Credencial: password123
```

### 10. Validar banco e schema
```sql
SELECT datname FROM pg_database WHERE datname = 'liceu_core_os';
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'public';
```

### 11. Não usar 127.0.0.1 em container
❌ DATABASE_URL: `postgresql://...@127.0.0.1:...`
✓ DATABASE_URL: `postgresql://...@db_core_os:...`

### 12. Execução fora do Docker
Se CEA executa no HOST e db_core_os em container:
```bash
# HOST: Usar porta exposta
DATABASE_URL=postgresql://admin:password123@localhost:5542/liceu_core_os
```

---

## SCRIPT DE VALIDAÇÃO

### Instalação de dependências
```bash
pip install psycopg2-binary
```

### Executar validação
```bash
# Com script de diagnóstico:
bash validate_canonical_connectivity.sh

# Ou diretamente com Python:
export DB_HOST=db_core_os
export DB_PORT=5432
export DB_NAME=liceu_core_os
export DB_USER=admin
export DB_PASSWORD=password123
python3 validate_canonical_connectivity.py
```

### Validação esperada
```json
{
  "gate": "CANONICAL_DATABASE_CONNECTIVITY",
  "db_host": "db_core_os",
  "db_port": 5432,
  "db_name": "liceu_core_os",
  "schema": "public",
  "dns_resolution_valid": true,
  "tcp_connection_valid": true,
  "postgres_connection_valid": true,
  "canonical_read_valid": true,
  "w89_event_visible": true,
  "w91_event_visible": true,
  "status": "PASS"
}
```

---

## REMEDIAÇÕES

### Se: DNS falha (`dns_resolution_valid: false`)
**Cenário**: `getent hosts db_core_os` falha

**Solução 1: Verificar rede Docker**
```bash
# Verificar se liceu-net existe
docker network ls | grep liceu-net

# Se não existe, criar:
docker network create liceu-net --driver bridge
```

**Solução 2: Reiniciar Docker Compose**
```bash
docker-compose down
docker-compose up -d
# Aguardar healthchecks
```

**Solução 3: Forçar rede em novo serviço**
```yaml
services:
  seu_servico:
    networks:
      - liceu-net  # ← Adicionar OBRIGATORIAMENTE
```

---

### Se: TCP falha (`tcp_connection_valid: false`)
**Cenário**: `nc -zv db_core_os 5432` falha

**Verificar status do container**
```bash
docker ps | grep db_core_os
docker logs db_core_os | tail -20
```

**Iniciar db_core_os se parado**
```bash
docker-compose up -d db_core_os
```

**Aguardar healthcheck**
```bash
docker ps --filter "name=db_core_os" \
  --format "table {{.Names}}\t{{.Status}}"
# Deve estar: "Up X seconds (healthy)"
```

---

### Se: PostgreSQL falha (`postgres_connection_valid: false`)
**Cenário**: Credenciais erradas ou banco inacessível

**Verificar credenciais no docker-compose**
```bash
grep -A 5 "db_core_os:" docker-compose.yml | grep POSTGRES
```

**Testando conexão manualmente**
```bash
# De um container na rede liceu-net:
docker exec <any_container> psql -h db_core_os -U admin -d liceu_core_os -c "SELECT 1"
# Senha: password123
```

**Se usuário/senha está incorreta**
Editar docker-compose.yml e regenerar volumes:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d db_core_os
```

---

### Se: Canonical read falha (`canonical_read_valid: false`)
**Cenário**: Banco conecta, mas immutable_events não existe

**Verificar estrutura do banco**
```bash
docker exec db_core_os psql -U admin -d liceu_core_os -c "\dt public.*"
```

**Se tabelas não existem**
Executar migrations:
```bash
docker-compose exec backend alembic upgrade head
# Ou similar conforme seu setup
```

---

### Se: CEA executa no HOST (fora do Docker)
**Cenário**: docker-compose executa em container, CEA em host

**Solução**
```bash
# HOST: Usar porta exposta (5542), não container DNS
export DATABASE_URL="postgresql://admin:password123@localhost:5542/liceu_core_os"

# NÃO use db_core_os (não resolve no host)
# NÃO use localhost:5432 (porta interna)
```

**Validar de fora do Docker**
```bash
psql postgresql://admin:password123@localhost:5542/liceu_core_os -c "SELECT 1"
```

---

## CHECKLIST DE REMEDIAÇÃO

- [ ] Verificar docker-compose.yml (db_core_os definido)
- [ ] Confirmar rede liceu-net (bridge driver)
- [ ] Iniciar db_core_os e aguardar healthy
- [ ] Adicionar `networks: [liceu-net]` em todos os consumidores
- [ ] Executar `docker-compose down && docker-compose up -d`
- [ ] Aguardar todos os healthchecks passarem
- [ ] Executar validação: `bash validate_canonical_connectivity.sh`
- [ ] Verificar resultado JSON (status == PASS)
- [ ] Testar acesso de cada monólito: CEA, ECONOTECH, FORNECEDORES, etc.

---

## CONSUMIDORES DO BACKBONE CANÔNICO

Todos os seguintes serviços PRECISAM acessar `db_core_os` para canonical events:

1. **CEA INVESTIMENTOS** (db_cea_investimentos)
2. **ECONOTECH** (db_econo_tech)
3. **FORNECEDORES** (db_erp_fornecedores)
4. **BIM ARCH ENG** (db_bim_arqu_eng)
5. **ARCHIMEDES** (db_archimedes)
6. **OPERA / HUB CONTABIL** (db_hub_contabil)
7. **CEFEIDA** (db_cefeida)
8. **P&D.IA** (db_pdi_ia)
9. **CDVIRTUAL** (db_cdvirtual)
10. **INVEST.TECH** (db_invest_tech)
11. **ACADEMIA.SABER** (db_academia_saber)
12. **GTAMKT** (db_gtamkt)
13. **JURIDICOTECH** (db_juridicotech)
14. **JOH.BRASILEIRO** (db_joh_brasileiro)

---

## REFERÊNCIAS

- **Arquivo Conforme**: `/docker-compose.yml` (linhas 235-249)
- **Rede Oficial**: `liceu-net` (bridge driver)
- **Porta Exposta**: `5542` (localhost:5542 para host-side)
- **Porta Interna**: `5432` (db_core_os:5432 para container-side)
- **Banco Canônico**: `liceu_core_os`
- **Schema**: `public`
- **Usuário**: `admin` (credencial vinda do ambiente)

---

## NÃO FAZER

❌ Não alterar novamente a lógica W92
❌ Não criar banco paralelo de fallback
❌ Não criar fallback para localhost (usa apenas host resolution)
❌ Não hardcodar credenciais (use variáveis de ambiente)
❌ Não usar memória como persistência substituta
❌ Não usar 127.0.0.1 dentro de containers
❌ Não remover `liceu-net` ou mudar driver

---

## SUPORTE

Se a validação falhar após todas as remediações:
1. Consultar: `docker logs db_core_os`
2. Consultar: `docker logs <consumer_service>`
3. Executar: `docker network inspect liceu-net`
4. Executar: `docker ps -a` (verificar se todos os serviços estão up)
5. Contactar: Equipe de Infraestrutura / DevOps

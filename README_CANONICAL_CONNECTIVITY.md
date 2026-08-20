# CANONICAL_DATABASE_CONNECTIVITY - Guia de Operação

## Visão Geral

Este conjunto de scripts valida e remedia a conectividade de rede entre os monólitos consumidores (CEA, ECONOTECH, FORNECEDORES, BIM ARCH ENG, ARCHIMEDES, OPERA, etc.) e o **Canonical Event Store** (`db_core_os:5432/liceu_core_os`).

### Arquivos Fornecidos

1. **validate_canonical_connectivity.sh** - Script de diagnóstico (bash)
2. **validate_canonical_connectivity.py** - Validador de conectividade (Python)
3. **remediate_canonical_connectivity.py** - Script de remediação automatizada (Python)
4. **CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md** - Guia técnico detalhado
5. **README_CANONICAL_CONNECTIVITY.md** - Este arquivo

---

## Início Rápido

### 1. Instalar dependências
```bash
pip install psycopg2-binary pyyaml
```

### 2. Validar conectividade
```bash
bash validate_canonical_connectivity.sh
```

**Esperado**: 
```
✅ CANONICAL_DATABASE_CONNECTIVITY VALIDADO COM SUCESSO
Status: PASS
```

**Se falhar**:
```
❌ FALHA NA CONECTIVIDADE CANÔNICA
Consulte: CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json
```

### 3. Se falhar, remediar automaticamente
```bash
python3 remediate_canonical_connectivity.py
```

O script irá:
- Carregar docker-compose.yml
- Adicionar rede liceu-net (se não existir)
- Configurar todos os consumidores na rede
- Adicionar healthchecks
- Validar credenciais
- Reiniciar docker-compose
- Aguardar healthchecks

---

## Fluxo Operacional Completo

### Passo 1: Validação Inicial
```bash
bash validate_canonical_connectivity.sh
```

**Saída esperada**:
```
[ETAPA 1/5] Verificando docker-compose.yml...
✓ docker-compose.yml encontrado

[ETAPA 2/5] Verificando se db_core_os está definido...
✓ Serviço db_core_os encontrado
  ✓ container_name: db_core_os
  ✓ POSTGRES_DB: liceu_core_os
  ✓ POSTGRES_USER: admin

[ETAPA 3/5] Verificando configuração da rede liceu-net...
✓ Rede liceu-net definida no docker-compose

[ETAPA 4/5] Verificando dependências de db_core_os...
✓ Há X serviço(s) dependendo de db_core_os

[ETAPA 5/5] Executando validação de conectividade...
✓ DNS resolution OK: db_core_os -> 172.18.0.4
✓ TCP connection OK: db_core_os:5432
✓ PostgreSQL connection OK
✓ immutable_events encontrada: N registros

[RESULTADO FINAL]
✅ CANONICAL_DATABASE_CONNECTIVITY VALIDADO COM SUCESSO
```

### Passo 2: Se Falhar, Remediar
```bash
python3 remediate_canonical_connectivity.py
```

**Saída esperada**:
```
[REMEDIAÇÃO 1/5] Garantindo rede liceu-net...
  ✓ Rede liceu-net já existe e está configurada corretamente

[REMEDIAÇÃO 2/5] Garantindo db_core_os na rede liceu-net...
  ✓ db_core_os já está na rede liceu-net

[REMEDIAÇÃO 3/5] Adicionando consumidores à rede liceu-net...
  ✓ backend adicionado à rede liceu-net
  ✓ john-crm adicionado à rede liceu-net
  ✓ john-engine adicionado à rede liceu-net
  ...

[REMEDIAÇÃO 4/5] Garantindo healthcheck para db_core_os...
  ✓ Healthcheck já está configurado

[REMEDIAÇÃO 5/5] Validando credenciais...
  ✓ POSTGRES_DB: liceu_core_os
  ✓ POSTGRES_USER: admin
  ✓ POSTGRES_PASSWORD: password123

[REMEDIAÇÃO FINAL] Regenerando docker-compose.yml...
  ✓ docker-compose.yml atualizado com sucesso

[RESTART] Reiniciando docker-compose...
  • Parando serviços...
  • Iniciando serviços...
  ✓ docker-compose reiniciado
  • Aguardando healthchecks...
    ✓ db_core_os healthy

✅ REMEDIAÇÃO CONCLUÍDA COM SUCESSO
```

### Passo 3: Validar Novamente
```bash
bash validate_canonical_connectivity.sh
```

Deve retornar `✅ CANONICAL_DATABASE_CONNECTIVITY VALIDADO COM SUCESSO`

---

## Verificações Manuais

Se desejar validar manualmente sem usar os scripts:

### Verificar se db_core_os está rodando
```bash
docker ps | grep db_core_os
```

Esperado:
```
5dae8f... postgres:15  "docker-entrypoint..." 2 minutes ago  Up 2 minutes (healthy)
```

### Verificar rede
```bash
docker network ls | grep liceu-net
docker network inspect liceu-net
```

### Testar DNS dentro de um container
```bash
docker exec <any_consumer_container> getent hosts db_core_os
```

Esperado:
```
172.18.0.4  db_core_os
```

### Testar TCP
```bash
docker exec <any_consumer_container> nc -zv db_core_os 5432
```

Esperado:
```
Connection to db_core_os 5432 port [tcp/*] succeeded!
```

### Testar conexão PostgreSQL
```bash
docker exec <any_consumer_container> psql -h db_core_os -U admin -d liceu_core_os -c "SELECT 1"
```

Esperado:
```
 ?column?
----------
        1
(1 row)
```

### Verificar eventos
```bash
docker exec db_core_os psql -U admin -d liceu_core_os -c "SELECT COUNT(*) FROM public.immutable_events;"
```

Esperado:
```
 count
-------
    N  (número de eventos)
(1 row)
```

---

## Interpretação de Resultados

### Status PASS
```json
{
  "status": "PASS",
  "dns_resolution_valid": true,
  "tcp_connection_valid": true,
  "postgres_connection_valid": true,
  "canonical_read_valid": true
}
```
✅ Tudo funcionando normalmente

### Status BLOCKED (DNS)
```json
{
  "status": "BLOCKED",
  "dns_resolution_valid": false,
  "errors": ["DNS resolution FAILED: db_core_os não resolveu"]
}
```
**Problema**: db_core_os não resolve em DNS
**Solução**: Verificar rede Docker e reiniciar

### Status BLOCKED (TCP)
```json
{
  "status": "BLOCKED",
  "tcp_connection_valid": false,
  "errors": ["TCP connection FAILED: Porta 5432 não respondeu"]
}
```
**Problema**: Container db_core_os não está acessível
**Solução**: `docker ps | grep db_core_os` e `docker logs db_core_os`

### Status BLOCKED (PostgreSQL)
```json
{
  "status": "BLOCKED",
  "postgres_connection_valid": false,
  "errors": ["PostgreSQL connection FAILED: ..."]
}
```
**Problema**: Credenciais erradas ou banco não iniciou
**Solução**: Verificar credenciais no docker-compose e logs

---

## Troubleshooting

### Problema 1: "db_core_os não resolve"
```bash
# Verificar se rede existe
docker network ls | grep liceu-net

# Se não existe, criar
docker network create liceu-net --driver bridge

# Reiniciar compose
docker-compose down
docker-compose up -d
```

### Problema 2: "TCP connection refused"
```bash
# Verificar se container está rodando
docker ps | grep db_core_os

# Ver logs
docker logs db_core_os

# Se parado, iniciar
docker-compose up -d db_core_os

# Aguardar healthy (até 30 segundos)
docker ps --filter "name=db_core_os" --format "table {{.Names}}\t{{.Status}}"
```

### Problema 3: "PostgreSQL connection failed - credenciais"
```bash
# Verificar credenciais no docker-compose
grep -A 10 "db_core_os:" docker-compose.yml | grep POSTGRES

# Se estão erradas, editar docker-compose.yml
nano docker-compose.yml

# Remover volumes e recrear
docker-compose down -v
docker-compose up -d db_core_os
```

### Problema 4: "CEA executa no host (fora do Docker)"
```bash
# Usar porta exposta (5542) ao invés de hostname
export DATABASE_URL="postgresql://admin:password123@localhost:5542/liceu_core_os"

# Testar
psql "$DATABASE_URL" -c "SELECT 1"
```

### Problema 5: "immutable_events não encontrada"
```bash
# Conectar ao banco
docker exec db_core_os psql -U admin -d liceu_core_os

# Verificar tabelas
\dt public.*

# Se vazio, executar migrations
docker-compose exec backend alembic upgrade head
```

---

## Monitoramento Contínuo

### Verificar saúde regularmente
```bash
# Cron job para validar a cada hora
0 * * * * /path/to/validate_canonical_connectivity.sh >> /var/log/canonical_connectivity.log 2>&1
```

### Monitorar logs
```bash
# Monitorar db_core_os
docker logs -f db_core_os

# Monitorar consumidores
docker logs -f cea_investimentos_api
docker logs -f econo_tech_api
```

---

## Checklist Pré-Deploy

Antes de fazer deploy em produção:

- [ ] Executar `bash validate_canonical_connectivity.sh`
- [ ] Confirmar resultado: Status PASS
- [ ] Testar acesso de cada monólito manualmente
- [ ] Verificar `docker logs db_core_os` (sem erros)
- [ ] Verificar eventos em `immutable_events` (count > 0)
- [ ] Testar failover de db_core_os (stop/start)
- [ ] Executar stress test se disponível
- [ ] Documentar tempo de validação

---

## Referências Rápidas

| Comando | Descrição |
|---------|-----------|
| `bash validate_canonical_connectivity.sh` | Validar conectividade completa |
| `python3 validate_canonical_connectivity.py` | Executar apenas Python validator |
| `python3 remediate_canonical_connectivity.py` | Remediar automaticamente |
| `docker ps \| grep db_core_os` | Verificar status do container |
| `docker logs db_core_os` | Ver logs do PostgreSQL |
| `docker network inspect liceu-net` | Inspecionar rede Docker |
| `docker exec <container> getent hosts db_core_os` | Testar DNS |
| `docker exec <container> psql -h db_core_os -U admin -d liceu_core_os -c "SELECT 1"` | Testar conexão |

---

## Contato & Suporte

Se o problema persistir após todas as remediações, colete:

1. Saída de `bash validate_canonical_connectivity.sh`
2. Conteúdo de `CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json`
3. Saída de `docker logs db_core_os | tail -100`
4. Saída de `docker ps -a`
5. Saída de `docker network inspect liceu-net`
6. Versão do Docker: `docker --version`
7. Versão do Docker Compose: `docker-compose --version`

Contacte a equipe de DevOps/Infraestrutura com essas informações.

---

## Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | 2026-08-20 | Versão inicial - Validação completa de conectividade canônica |

---

## Licença e Disclaimer

Estes scripts são parte da solução LICEU 6.0 CONSTRUTORA VIRTUAL.

⚠️ **IMPORTANTE**: Não altere manualmente docker-compose.yml se os scripts de remediação estiverem rodando.
⚠️ **BACKUP**: Os scripts criam backups automáticos (`.yml.bak`). Consulte-os se necessário.

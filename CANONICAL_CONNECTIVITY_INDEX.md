# CANONICAL_DATABASE_CONNECTIVITY - Index & Navigation

## 🎯 Comece Aqui

**Objetivo**: Garantir conectividade de rede entre monólitos e Canonical Event Store (`db_core_os:5432/liceu_core_os`)

**Tempo Estimado**: 5-15 minutos (validação) + 10-30 minutos (remediação se necessário)

---

## 🚀 Início Rápido (Escolha Um)

### Opção A: Interactive Quick Start (Recomendado)
```bash
bash canonical_connectivity_quickstart.sh
```
Neste script você escolhe entre:
- ✅ Validar conectividade
- 🔧 Remediar problemas
- 🧪 Testes manuais
- 📚 Ver documentação

### Opção B: Validar Diretamente
```bash
bash validate_canonical_connectivity.sh
```
Resultado esperado: `✅ PASS`

### Opção C: Testar Manualmente
```bash
docker ps | grep db_core_os
docker logs db_core_os
docker network inspect liceu-net
```

---

## 📚 Documentação por Caso de Uso

### 👤 Eu Sou Um... (Escolha seu Perfil)

#### 🏃‍♂️ DevOps / Engenheiro de Infraestrutura
**Objetivo**: Validar e corrigir configuração de rede

**Arquivos**:
1. [`CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md`](#canonical_database_connectivity_guideomd) - Guia técnico completo com 12 etapas
2. [`validate_canonical_connectivity.sh`](#validate_canonical_connectivitysh) - Script de diagnóstico
3. [`remediate_canonical_connectivity.py`](#remediate_canonical_connectivitypy) - Automação de correção

**Workflow**:
```
Ler guia técnico 
  ↓
Executar validação 
  ↓
Se falhar → Executar remediação 
  ↓
Validar novamente
```

#### 🤖 DevOps / CI-CD Engineer
**Objetivo**: Integrar validação em pipeline de deploy

**Arquivos**:
1. [`validate_canonical_connectivity.py`](#validate_canonical_connectivitypy) - Retorna JSON (`status: PASS|BLOCKED`)
2. [`CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json`](#resultado-json) - Output estruturado

**Integração Exemplo**:
```yaml
# .github/workflows/deploy.yml
- name: Validate Canonical Connectivity
  run: python3 validate_canonical_connectivity.py
  
- name: Check Result
  run: |
    jq '.status' CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json | grep -q PASS
```

#### 📊 Director / Project Manager
**Objetivo**: Entender o problema e status

**Arquivos**:
1. [`CANONICAL_CONNECTIVITY_EXECUTIVE_SUMMARY.md`](#canonical_connectivity_executive_summarymd) - Resumo em 1 página
2. [`CANONICAL_FEDERATION_BACKBONE_REPORT.md`](#canonical_federation_backbone_reportmd) - Contexto mais amplo

**Leitura Rápida**:
- ✅ Status: Tudo implementado, pronto para testar
- ⏱️ Tempo: 5-15 minutos para validar
- 🎯 Impacto: Garante acesso de 14+ monólitos ao Canonical Event Store

#### 👨‍💻 Developer / Monolith Owner
**Objetivo**: Validar que meu serviço acessa `db_core_os` corretamente

**Arquivos**:
1. [`README_CANONICAL_CONNECTIVITY.md`](#readme_canonical_connectivitymd) - Guia operacional
2. [`validate_canonical_connectivity.sh`](#validate_canonical_connectivitysh) - Teste seu acesso

**Teste Rápido**:
```bash
# De dentro do seu container:
docker exec <seu_container> psql -h db_core_os -U admin -d liceu_core_os -c "SELECT COUNT(*) FROM public.immutable_events"

# Esperado: número de eventos
```

#### 🆘 SRE / On-Call Support
**Objetivo**: Diagnosticar e corrigir problemas em produção

**Arquivos**:
1. [`CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md`](#canonical_database_connectivity_guideomd) - Seção "Troubleshooting"
2. [`validate_canonical_connectivity.sh`](#validate_canonical_connectivitysh) - Diagnóstico rápido
3. [`remediate_canonical_connectivity.py`](#remediate_canonical_connectivitypy) - Correção automática

**Resposta a Incidente**:
```
1. Executar validação → JSON status
2. Ler erro específico em CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json
3. Consultar troubleshooting no guia técnico
4. Executar remediação se aplicável
5. Validar novamente
6. Comunicar status
```

---

## 📂 Estrutura de Arquivos

```
/workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/
│
├─ 🚀 QUICK START
│  ├─ canonical_connectivity_quickstart.sh        [COMECE AQUI - Menu Interativo]
│  └─ README_CANONICAL_CONNECTIVITY.md            [Guia Rápido]
│
├─ 🔍 VALIDAÇÃO
│  ├─ validate_canonical_connectivity.sh          [Script bash - Orquestra validação]
│  └─ validate_canonical_connectivity.py          [Script Python - Validador core]
│
├─ 🔧 REMEDIAÇÃO
│  ├─ remediate_canonical_connectivity.py         [Automação de correção]
│  └─ CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json [Output da validação]
│
├─ 📚 DOCUMENTAÇÃO
│  ├─ CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md    [Guia Técnico - 12 etapas]
│  ├─ CANONICAL_CONNECTIVITY_EXECUTIVE_SUMMARY.md [Resumo Executivo - 1 página]
│  ├─ README_CANONICAL_CONNECTIVITY.md            [Guia Operacional]
│  └─ CANONICAL_CONNECTIVITY_INDEX.md             [Este arquivo]
│
└─ 📊 REFERÊNCIA
   ├─ CANONICAL_FEDERATION_BACKBONE_REPORT.md    [Contexto arquitetural]
   └─ CANONICAL_FEDERATION_BACKBONE_GATE_RESULT.json [Resultado anterior]
```

---

## 🔗 Guia Detalhado por Arquivo

### 🚀 `canonical_connectivity_quickstart.sh`
**O quê**: Menu interativo com todas as opções  
**Quando usar**: Na primeira vez, para se familiarizar  
**Tempo**: 1-2 minutos  
**Comando**: `bash canonical_connectivity_quickstart.sh`  

**Oferece**:
- ✅ Verificação de pré-requisitos
- 🔍 Validação automática
- 🔧 Remediação automática
- 🧪 Testes manuais
- 📚 Links para documentação

---

### 🔍 `validate_canonical_connectivity.sh`
**O quê**: Script bash que orquestra a validação completa  
**Quando usar**: Sempre que precisa validar  
**Tempo**: 3-5 minutos  
**Comando**: `bash validate_canonical_connectivity.sh`  

**Verifica**:
1. docker-compose.yml existe e tem db_core_os
2. Rede liceu-net configurada
3. Credenciais corretas
4. Executa validador Python
5. Retorna relatório legível

**Saída**: Relatório textual + JSON

---

### 🐍 `validate_canonical_connectivity.py`
**O quê**: Validador Python core (6 etapas)  
**Quando usar**: Quando precisa apenas dos dados JSON ou CI/CD  
**Tempo**: 2-3 minutos  
**Comando**: `python3 validate_canonical_connectivity.py`  

**Etapas**:
1. DNS resolution test
2. TCP connectivity test
3. PostgreSQL authentication test
4. Canonical read test
5. Docker network validation
6. Event visibility check

**Saída**: JSON estruturado com status PASS/BLOCKED

**Exemplo Resultado**:
```json
{
  "status": "PASS",
  "dns_resolution_valid": true,
  "tcp_connection_valid": true,
  "postgres_connection_valid": true,
  "canonical_read_valid": true,
  "w89_event_visible": true,
  "w91_event_visible": true
}
```

---

### 🔧 `remediate_canonical_connectivity.py`
**O quê**: Automatiza correção de problemas  
**Quando usar**: Se validação retornar BLOCKED  
**Tempo**: 5-10 minutos (+ restart de containers)  
**Comando**: `python3 remediate_canonical_connectivity.py`  

**O Que Faz**:
1. Garante rede liceu-net
2. Adiciona db_core_os à rede
3. Adiciona consumidores à rede
4. Valida healthcheck
5. Regenera docker-compose.yml
6. Reinicia containers
7. Aguarda healthchecks

**Saída**: docker-compose.yml atualizado + confirmação

---

### 📖 `CANONICAL_DATABASE_CONNECTIVITY_GUIDE.md`
**O quê**: Guia técnico completo (mapa 1:1 das 12 etapas do diagnóstico)  
**Quando ler**: Antes de fazer mudanças, para entender o contexto  
**Tempo**: 15-20 minutos  

**Seções**:
- Diagnóstico (o que foi encontrado)
- Configuração do docker-compose.yml
- 12 etapas de validação (detalhadas)
- Script de validação (como funciona)
- Remediações (por tipo de erro)
- Checklist
- NÃO FAZER (importante!)
- Referências

---

### 📋 `CANONICAL_CONNECTIVITY_EXECUTIVE_SUMMARY.md`
**O quê**: Resumo executivo em 1 página  
**Quando ler**: Para entender o problema e status em 5 minutos  
**Tempo**: 5 minutos  

**Contém**:
- Objetivo (1 linha)
- Diagnóstico (o que está certo/errado)
- Solução (o que foi implementado)
- Como usar (3 passos)
- Próximos passos
- Diagrama da arquitetura

---

### 📚 `README_CANONICAL_CONNECTIVITY.md`
**O quê**: Guia operacional com exemplos práticos  
**Quando ler**: Quando precisa executar operações ou troubleshootar  
**Tempo**: 10-15 minutos  

**Contém**:
- Início rápido
- Fluxo operacional completo
- Verificações manuais
- Interpretação de resultados
- Troubleshooting por tipo de erro
- Monitoramento contínuo
- Checklist pré-deploy

---

### 📊 `CANONICAL_FEDERATION_BACKBONE_REPORT.md`
**O quê**: Relatório arquitetural mais amplo (contexto)  
**Quando ler**: Para entender o projeto maior  
**Tempo**: 20 minutos  

**Contexto**: Federação, routing, discovery, replicação

---

### 💾 `CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json`
**O quê**: Output estruturado da validação Python  
**Quando gerar**: Após executar `validate_canonical_connectivity.py`  
**Uso**: Parsing em scripts, CI/CD, alertas  

**Exemplo**:
```json
{
  "gate": "CANONICAL_DATABASE_CONNECTIVITY",
  "db_host": "db_core_os",
  "status": "PASS" ou "BLOCKED",
  "errors": ["lista de erros se houver"],
  "dns_resolution_valid": true/false,
  "tcp_connection_valid": true/false,
  "postgres_connection_valid": true/false,
  "canonical_read_valid": true/false
}
```

---

## 🎓 Matriz de Decisão

```
┌─────────────────────────────────────────────────────────────────┐
│ QUE DEVO FAZER? (Decision Tree)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Primeira vez? → canonical_connectivity_quickstart.sh             │
│                                                                   │
│ Preciso validar? → bash validate_canonical_connectivity.sh       │
│                                                                   │
│ Validação falhou? → python3 remediate_canonical_connectivity.py  │
│                                                                   │
│ Preciso entender o problema? → Ler GUIDE.md (técnico)            │
│                                                                   │
│ Sou gerente/director? → Ler EXECUTIVE_SUMMARY.md (1 página)      │
│                                                                   │
│ Preciso fazer deploy? → Checklist em README_CANONICAL_*.md       │
│                                                                   │
│ Há um incidente? → Troubleshooting em GUIDE.md                   │
│                                                                   │
│ Preciso integrar em CI/CD? → validate_canonical_connectivity.py  │
│                             → Ler output JSON                    │
│                                                                   │
│ Preciso de backup antes de remediar? → Automático (*.yml.bak)    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ Tempos Estimados

| Atividade | Tempo | Comando |
|-----------|-------|---------|
| Verificar pré-requisitos | 30s | `bash canonical_connectivity_quickstart.sh` |
| Validar conectividade | 3-5min | `bash validate_canonical_connectivity.sh` |
| Leitura rápida (1 página) | 5min | Ler `EXECUTIVE_SUMMARY.md` |
| Remediação automática | 5-10min | `python3 remediate_canonical_connectivity.py` |
| Leitura técnica completa | 20-30min | Ler `GUIDE.md` |
| Troubleshooting manual | 10-30min | Depende do problema |
| Pré-deploy checklist | 10-15min | Ler `README_*.md` |

---

## 🆘 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "db_core_os não resolve" | `docker-compose up -d && bash validate_canonical_connectivity.sh` |
| "TCP connection refused" | `docker logs db_core_os` e aguardar healthcheck |
| "PostgreSQL auth failed" | Verificar docker-compose.yml credenciais |
| "Script não executa" | `chmod +x *.sh` e verificar Python 3 instalado |
| "CEA em host não conecta" | Usar `localhost:5542` não `db_core_os:5432` |
| "immutable_events não existe" | Executar migrations ou consultar DBA |

---

## ✅ Checklist de Sucesso

Após todas as operações:

- [ ] Executei `bash canonical_connectivity_quickstart.sh`
- [ ] Validação retornou `Status: PASS`
- [ ] Não há erros em `CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json`
- [ ] Todos os 14+ monólitos podem acessar `db_core_os`
- [ ] `docker logs db_core_os` não mostra erros
- [ ] Documentei resultado para auditoria
- [ ] Pronto para deploy em produção

---

## 📞 Próximos Passos

1. **Agora**: `bash canonical_connectivity_quickstart.sh`
2. **Depois**: Seguir as instruções do menu interativo
3. **Validar**: Confirmar que status é PASS
4. **Deploy**: Seguir checklist em `README_*.md`
5. **Monitor**: Adicionar validação em CI/CD

---

## 📧 Contato & Suporte

Se encontrar problemas após consultar toda a documentação:

1. Coletar saída de `validate_canonical_connectivity.sh`
2. Incluir `CANONICAL_CONNECTIVITY_VALIDATION_RESULT.json`
3. Incluir output de `docker logs db_core_os`
4. Contactar: Equipe DevOps / Infraestrutura

---

## 🏷️ Tags e Referências

- **Monólitos**: CEA, ECONOTECH, FORNECEDORES, BIM ARCH ENG, ARCHIMEDES, OPERA, etc. (14+)
- **Canonical Event Store**: `db_core_os:5432/liceu_core_os` (banco + schema public)
- **Rede Docker**: `liceu-net` (bridge driver)
- **Diagnóstico**: 12 etapas mapeadas em `GUIDE.md`
- **Automação**: 5 etapas de remediação em `remediate_*.py`
- **Validação**: 6 etapas de teste em `validate_*.py`

---

**Última atualização**: 2026-08-20  
**Versão**: 1.0  
**Status**: Pronto para uso ✅

---

## 🎯 TL;DR (Muito Longo; Não Lerei)

```bash
# Instale dependências (1 vez)
pip install psycopg2-binary pyyaml

# Valide conectividade
bash validate_canonical_connectivity.sh

# Se falhar, remedie
python3 remediate_canonical_connectivity.py

# Valide novamente
bash validate_canonical_connectivity.sh

# Esperado: Status PASS ✅
```

---

Está pronto! Comece com: `bash canonical_connectivity_quickstart.sh`

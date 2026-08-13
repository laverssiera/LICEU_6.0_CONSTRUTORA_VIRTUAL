# John — IA Interpretativa do LICEU 6.0

## Posição na Arquitetura

John **não é tomador de decisão**. É uma camada de interpretação e interface.

```
Sistema de Eventos → BRAIN_LIB (cálculo) → SDK → Runtime → John → Ação/Resposta
```

## Princípio Fundamental

**JOHN NÃO DECIDE. JOHN INTERPRETA E EXECUTA SCRIPTS.**

### Quem realmente decide?

- **CEFEIDA**: regras de negócio, modelos de viabilidade
- **Governança**: políticas e limites
- **Dados reais**: histórico de projetos
- **Usuário final**: aprova ou rejeita recomendações

## John Interno (Runtime Engine)

Responsável por interpretar eventos do ecossistema e gerar ações inteligentes.

### Localização

```
liceu-6.0/runtime/john_engine/
```

### Responsabilidades

1. Recebe evento do barramento
2. Consulta CEFEIDA/SDK se necessário
3. Gera recomendação ou ação
4. Retorna para o fluxo apropriado

### Exemplo de Fluxo

**Entrada:**
```json
{
  "type": "project.risk_detected",
  "project_id": "proj-123",
  "risk_score": 0.78
}
```

**Processamento (John):**
- Score 0.78 → risco alto
- Consultar SDK para validar
- Preparar recomendação

**Saída:**
```json
{
  "message": "Risco elevado detectado (78%)",
  "action": "notify_manager",
  "priority": "high",
  "recommendation": "Reforçar equipe, revisar cronograma"
}
```

### Eventos Mapeados

| Evento | Ação | Prioridade |
|--------|------|-----------|
| `project.risk_detected` | notify_manager | high |
| `payment.delayed` | escalate_financial | high |
| `task.overdue` | notify_manager | high |
| `supply_chain.alert` | notify_procurement | high |
| `audit.finding` | create_action_item | medium-critical |
| `lead.created` | log_interaction | normal |

## John Externo (CRM + SDR)

Responsável por conversar com clientes, qualificar leads e gerar eventos de entrada.

### Localização

```
modules/crm/john_crm/
```

### Responsabilidades

1. Comunica com clientes (chat, WhatsApp, etc)
2. Detecta intenção
3. Qualifica lead
4. Publica evento `crm.lead.created` para o core
5. Acompanha a conversão

### Fluxo Completo

```
Cliente entra no site
    ↓
John: "Olá! O que você busca?"
    ↓
Cliente: "Quero construir 20 casas"
    ↓
John: "Incrível! Vou estruturar seu projeto.
       Estimativa: valor baseado em CEFEIDA
       Quer estudo de viabilidade?"
    ↓
Lead criado e publicado (evento)
    ↓
Runtime processa
    ↓
OPERA / CEA / P&D recebem tarefa
    ↓
Projeto nasce
```

### Detecção de Intenção

```python
intents = {
    "construction": ["construir", "obra", "casa", "prédio"],
    "investment": ["investir", "rendimento", "retorno"],
    "partnership": ["parceria", "colaborar", "negócio"],
    "financing": ["financiar", "crédito", "empréstimo"],
    "consulting": ["consultar", "orientação", "dúvida"]
}
```

### Score de Qualificação (0-100)

**Componentes:**
- Baseline: 50 pontos
- Detalhamento da mensagem: +10-20
- Intenção clara: +5-25
- Histórico/contexto: +5-10

**Decisão:**
- ≥75: qualified → atribuir a módulo
- 50-75: pending_info → solicitar mais dados
- <50: rejected → nurture list

## Banco de Dados do CRM

```
crm_leads
├── id, name, email, phone
├── interest, source, status
├── initial_score, final_score
├── assigned_module
├── created_at, qualified_at, converted_at
└── project_id, deal_id (após conversão)

crm_interactions
├── id, lead_id
├── type (message, call, email, suggestion)
├── content, john_response
├── sentiment, timestamp
└── duration_seconds

crm_conversions
├── lead_id → project_id, deal_id
├── deal_type, deal_value
└── conversion_date

crm_audit_log
├── lead_id, action, actor
├── details (JSONB)
└── timestamp
```

## Governança do John

### User Type: SYSTEM

No modelo RBAC do LICEU:

```
ROLES (padrão):
├── ADMIN_MASTER
├── BROKER
├── CLIENT
├── OWNER
├── INVESTOR
└── SYSTEM (JOHN) ✅
```

### Permissões de John

✅ **CAN DO:**
- Ler eventos do barramento
- Publicar eventos de lead/qualificação
- Atualizar scores de lead
- Gerar recomendações
- Notificar usuários
- Logar interações

❌ **CANNOT DO:**
- Acessar banco de dados diretamente
- Decidir sobre investimentos
- Alterar policies de governança
- Agir fora do event bus
- Executar ações sem log

### Auditoria Completa

Todo acesso de John é logado:

```json
{
  "lead_id": "lead-123",
  "action": "qualify_lead",
  "actor": "john_crm",
  "details": {
    "score": 78,
    "status": "qualified",
    "module": "OPERA"
  },
  "timestamp": "2026-04-30T10:30:00Z"
}
```

## Integração com o Ecossistema

### John → Events

```python
# JohnCRM qualifica lead
await john.qualify_lead(lead_id, interactions)

# Publica: crm.lead.qualified
{
  "lead_id": "lead-123",
  "final_score": 78,
  "status": "qualified",
  "assigned_module": "OPERA",
  "recommendation": "Pitch técnico pronto"
}
```

### Events → John (Runtime)

```python
# Runtime recebe evento
await runtime.process_event(event)

# Consulta John (interpretar)
interpretation = await john_engine.interpret(event)

# Executa ação
if interpretation["action"] == "notify_manager":
    await notify(interpretation["message"])
```

## Exemplos de Uso

### 1. Cliente Conversa (CRM)

```python
john = JohnCRM(nats_bus, sdk)

response = await john.chat(
    "Quero construir um condomínio com 50 casas",
    context={"source": "site", "email": "cliente@example.com"}
)

# Retorna:
{
    "response": "Vou estruturar seu projeto...",
    "lead_id": "lead-456",
    "intent": "construction",
    "score": 85  # Qualificado!
}
```

### 2. Sistema Detecta Risco (Runtime)

```python
event = {
    "type": "project.risk_detected",
    "project_id": "proj-789",
    "risk_score": 0.85
}

interpretation = await john_engine.interpret(event)

# Retorna:
{
    "message": "Risco crítico (85%)",
    "action": "notify_manager",
    "priority": "critical",
    "recommendation": "Parar obra, revisar completamente"
}
```

### 3. Lead Qualificado Vira Projeto

```python
# CRM qualificou com score 78
await john.qualify_lead("lead-123", interactions)

# Evento publicado: crm.lead.qualified
# Runtime recebe e inicia fluxo de projeto

# OPERA baixa tarefa: "Análise técnica - Condomínio 50 casas"
# CEA baixa tarefa: "Viabilidade financeira"
# P&D baixa tarefa: "Processos e padrões"
```

## Como John Não Erra

1. **Validação**: Sempre consulta SDK antes de recomendar
2. **Auditoria**: Todo ato é logado (quem, quando, o quê)
3. **Limite de Escopo**: Só interpreta, não decide
4. **Feedback Loop**: Usuário aprova/desaprova, John aprende
5. **Governança Estrita**: Não sai do barramento, não acessa BD direto

## Próximos Passos

- [ ] Implementar NLP melhor para detecção de intenção
- [ ] Integrar com WhatsApp Business API
- [ ] Dashboard de conversões (leads → projetos)
- [ ] ML para score refinado (histórico de conversões)
- [ ] Integration com Analytics (Mixpanel/Amplitude)

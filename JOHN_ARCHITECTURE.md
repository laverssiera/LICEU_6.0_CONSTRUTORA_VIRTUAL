# Arquitetura do John no LICEU 6.0

## Diagrama Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                      SITE / WHATSAPP                            │
├─────────────────────────────────────────────────────────────────┤
│                        Chat Interface                            │
│              (entrada de clientes) → John CRM                    │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   │ "Quero construir 20 casas"
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                       JOHN CRM (Externo)                         │
├─────────────────────────────────────────────────────────────────┤
│ • Detecta intenção                                              │
│ • Calcula score (qualificação)                                  │
│ • Gera resposta customizada                                     │
│ • Publica: crm.lead.created                                     │
│                                                                  │
│ "Estimativa: R$ 2M | Retorno: R$ 3.2M | Viabilidade?"          │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   │ Evento: crm.lead.created
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                      NATS EVENT BUS                              │
│         (liceu.events - barramento canonico)                     │
└──────────────────┬────────────────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ↓             ↓             ↓
   RUNTIME      OPERA          CEA
     │
     ↓
┌─────────────────────────────────────────────────────────────────┐
│                    JOHN ENGINE (Interno)                         │
├─────────────────────────────────────────────────────────────────┤
│ • Interpreta eventos do barramento                              │
│ • Consulta SDK/CEFEIDA                                          │
│ • Gera recomendações (SEM DECIDIR)                              │
│ • Loga todas as ações                                           │
│                                                                  │
│ Evento: project.risk_detected (78%)                             │
│ → Risco alto → Notificar gerente                                │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│              Command Center / Dashboard / Email / SMS             │
│                     (ações finais)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Fluxo Detalhado: Lead → Projeto

```
PASSO 1: Cliente Chega
├─ Site / WhatsApp
├─ John CRM: "Olá! O que você busca?"
└─ Cliente: "Construir 20 casas"

PASSO 2: John Qualifica
├─ Detecta: intent = "construction"
├─ Calcula: score = 85 (bem qualificado)
├─ Gera: "Vou estruturar seu projeto"
└─ Evento: crm.lead.created (85)

PASSO 3: Runtime Recebe
├─ Lê evento no barramento
├─ Cria entrada em crm_leads
├─ Atribui: assigned_module = "OPERA"
└─ Dispara: tarefas para OPERA/CEA/P&D

PASSO 4: Conversação Contínua
├─ John segue conversando
├─ "Qual seu orçamento?"
├─ "Qual cronograma?"
└─ Cada mensagem refina o score

PASSO 5: Qualificação Final
├─ John qualifica com histórico completo
├─ Final score: 82
├─ Status: "qualified"
└─ Evento: crm.lead.qualified

PASSO 6: Projeto Nasce
├─ OPERA: inicia estudo técnico
├─ CEA: viabilidade financeira
├─ P&D: processos e padrões
└─ Lead convertido em projeto

PASSO 7: Acompanhamento
├─ John monitora projeto
├─ Se risco sobe: alerta
├─ Se tarefa atrasa: escalação
└─ Tudo logado (auditoria)
```

## Posição no Event Hub

```
Produtor           NATS Bus              Consumidor
────────────────────────────────────────────────────

Site               
  └─ john.chat ───→ crm.lead.created ──→ Runtime
                                       ├→ OPERA
                                       ├→ CEA
                                       └→ P&D

Project          
  └─ risk ───────→ project.risk ──────→ Runtime
                                       ├→ John Engine
                                       └→ Notifications

CRM               
  └─ qualify ────→ crm.lead.qualified → Runtime
                  & Event Log

CCPI/Others       
  └─ audit ──────→ audit.finding ────→ John Engine
                                       ├→ Notifications
                                       └→ Audit Log
```

## Banco de Dados: CRM vs Core

```
┌──────────────────────┐     ┌──────────────────────┐
│   CRM Database       │     │   Core Database      │
├──────────────────────┤     ├──────────────────────┤
│ crm_leads            │     │ business_cases       │
│ crm_interactions     │ ←──→│ projects             │
│ crm_conversions      │     │ audit_events         │
│ crm_audit_log        │     │ financial_records    │
└──────────────────────┘     └──────────────────────┘
       ↑                               ↑
       │                               │
       └───── Linked via Event Bus ────┘
           (não consulta SQL direta)
```

## Governança do John

### UserType: SYSTEM

```
┌─────────────────┬────────────────┐
│ USER TYPE       │ EXAMPLE         │
├─────────────────┼────────────────┤
│ ADMIN_MASTER    │ CEO             │
│ BROKER          │ Agent           │
│ CLIENT          │ Comprador       │
│ INVENSTOR       │ Investidor      │
│ SYSTEM (JOHN)   │ john_crm, john_ │
│                 │ engine          │
└─────────────────┴────────────────┘
```

### RBAC do John

**✅ Pode fazer:**
- Ler todos os eventos
- Publicar eventos de lead/qualificação
- Atualizar score de lead
- Gerar recomendações
- Criar logs

**❌ Não pode:**
- Acessar BD direto
- Decidir sobre investimentos
- Alterar políticas de governança
- Executar fora do event bus

## Erro Evitar ❌

```javascript
// ❌ ERRADO - John acessando BD direto
const lead = await db.query("SELECT * FROM leads WHERE id = ?")
john.violateDatabaseEncapsulation(lead)

// ✅ CORRETO - Via event bus
const event = await bus.read("crm.lead.created")
john.processEvent(event)
```

```javascript
// ❌ ERRADO - John decidindo investimento
if (lead.score > 80) {
  await bank.transfer(leadData.account, businessAccount, leadData.value)
}

// ✅ CORRETO - John recomendando
if (lead.score > 80) {
  await bus.publish("recommendation.investment_ready", {
    lead_id, recommendation: "aprovado para pitch"
  })
}
```

## Checklist: John Funcionando Certo

- [ ] Lead cria evento (crm.lead.created)
- [ ] Runtime consome e processa
- [ ] John interpreta evento (risk, audit, etc)
- [ ] Recomendação é logada com auditoria
- [ ] Ação é disparada (notificação, escalação)
- [ ] Nada passa por acesso direto ao BD
- [ ] Tudo está no barramento
- [ ] Tudo é rastreável (audit_log)

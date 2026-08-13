# John Engine (Runtime)

Motor de interpretação que roda dentro do runtime do LICEU 6.0.

## Objetivo

Interpretar eventos do ecossistema e gerar ações/recomendações inteligentes sem tomar decisões.

## Operação Básica

```
evento → john_engine.interpret() → {message, action, priority, data} → execução
```

## Como Usar

```python
from liceu_6_0.runtime.john_engine import JohnInternal

# Instanciar
john = JohnInternal(brain_sdk=sdk, logger=logger)

# Processar evento
event = {
    "type": "project.risk_detected",
    "project_id": "proj-123",
    "risk_score": 0.78
}

result = await john.interpret(event)

# result:
{
    "message": "Risco elevado detectado no projeto proj-123 (score: 0.78)",
    "action": "notify_manager",
    "priority": "high",
    "data": {
        "project_id": "proj-123",
        "risk_score": 0.78,
        "recommendation": "Reforcar equipe, revisar cronograma, considerar pausa de obra"
    }
}
```

## Eventos Suportados

| Tipo | Handler | Ação |
|------|---------|------|
| `project.risk_detected` | `_handle_risk_detected` | Notificar gerente |
| `lead.created` | `_handle_lead_created` | Log interação |
| `payment.delayed` | `_handle_payment_delayed` | Escalar financeiro |
| `task.overdue` | `_handle_task_overdue` | Notificar gerente |
| `supply_chain.alert` | `_handle_supply_alert` | Notificar procurement |
| `audit.finding` | `_handle_audit_finding` | Criar action item |

## Severidade de Risco

```
risk_score < 0.6  → "medium"
risk_score 0.6-0.8 → "high"
risk_score > 0.8  → "critical"
```

## Recomendações por Risco

```
Crítico (>0.8):
  "Reforcar equipe, revisar cronograma, considerar pausa de obra"

Alto (0.6-0.8):
  "Reforcar equipe, aumentar supervisao, revisar recursos"

Médio (<0.6):
  "Manter vigilancia, monitoramento intensivo"
```

## Escalação

John **não escala diretamente**. Apenas marca a prioridade.

O fluxo é:

```
John (interpret) → {priority: "critical"}
    ↓
Runtime (dispatch) → enviar para canal apropriado
    ↓
Manager (approva) → executa ação
```

## Uso no Runtime Completo

```python
class LiceuRuntime:
    def __init__(self):
        self.john = JohnInternal(sdk=self.sdk)
        self.bus = EventBus(...)
    
    async def process_event(self, event):
        # Interpretar com John
        interpretation = await self.john.interpret(event)
        
        # Executar ação apropriada
        if interpretation["action"] == "notify_manager":
            await self._notify_manager(interpretation)
        elif interpretation["action"] == "escalate_financial":
            await self._escalate_to_finance(interpretation)
        # ...
```

## Não Fazer (❌)

- Deixar John acessar banco de dados
- Deixar John tomar decisões executivas
- Usar JohN fora do event bus
- Ignorar logs de auditoria de John

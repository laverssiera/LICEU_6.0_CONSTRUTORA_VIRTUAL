# Playbook: Evento Travado

## Sintoma
- Evento não processado, parado na fila ou DLQ.

## Diagnóstico
1. Verifique na DLQ se o evento está presente.
2. Consulte logs do monólito/processador responsável.
3. Cheque dependências (pipeline, contratos, etc).

## Ação
- Use o Control Plane para reprocessar o evento (`/control/reprocess_event`).
- Se falhar novamente, acione o SAGA Engine para compensação.
- Audite o motivo do travamento e registre no event_store.

## Comando rápido
```bash
curl -X POST http://localhost:8000/control/reprocess_event -H 'Content-Type: application/json' -d '{"event_id": "<ID_DO_EVENTO>"}'
```

# Playbook: Falha Financeira

## Sintoma
- Evento financeiro rejeitado, duplicado ou inconsistência no ledger.

## Diagnóstico
1. Verifique o event_store e financial_ledger para o pipeline/evento.
2. Consulte logs do policy engine e camada financeira.
3. Cheque se há compensações SAGA emitidas.

## Ação
- Use o Control Plane para reprocessar ou compensar evento.
- Se duplicidade, acione rollback lógico via SAGA.
- Audite toda intervenção.

## Comando rápido
```bash
curl -X POST http://localhost:8000/control/reprocess_event -H 'Content-Type: application/json' -d '{"event_id": "<ID_DO_EVENTO>"}'
```

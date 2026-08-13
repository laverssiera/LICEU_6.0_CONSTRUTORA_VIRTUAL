# Playbook: Pipeline Inconsistente

## Sintoma
- Pipeline parado em estado inválido ou não avança.

## Diagnóstico
1. Verifique o histórico de transições no pipeline_history.
2. Consulte eventos recentes no event_store.
3. Cheque se há overrides ou intervenções manuais.

## Ação
- Use o Control Plane para forçar transição (`/control/force_transition`).
- Audite o motivo e registre o responsável.
- Se necessário, pause o pipeline para investigação.

## Comando rápido
```bash
curl -X POST http://localhost:8000/control/force_transition -H 'Content-Type: application/json' -d '{"pipeline_id": "<ID>", "to_stage": "<STAGE>", "reason": "corrigir inconsistência", "approved_by": "<USUÁRIO>"}'
```

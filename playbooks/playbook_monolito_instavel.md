# Playbook: Monólito Instável

## Sintoma
- Monólito fora do ar, alta latência, erros de rede.

## Diagnóstico
1. Verifique métricas de erro e logs do monólito.
2. Consulte status no Control Plane (`/control/status`).
3. Cheque se há flags de chaos ativadas.

## Ação
- Use o Control Plane para desabilitar/reabilitar monólito (`/control/disable_monolith`).
- Acione incident response se necessário.
- Audite toda ação tomada.

## Comando rápido
```bash
curl -X POST http://localhost:8000/control/disable_monolith -H 'Content-Type: application/json' -d '{"monolith": "<NOME>"}'
```

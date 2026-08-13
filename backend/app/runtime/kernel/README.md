# Kernel Runtime

Este módulo implementa o orquestrador central do LICEU 6.0, responsável por:
- Ingestão de eventos
- Validação CORE-DNA
- Enforcement de governança
- Simulação e shadow
- Roteamento para executor
- Auditoria imutável
- Safety Mode

## Principais arquivos
- `runtime_kernel.py`: Classe principal do Kernel
- `enforcement.py`: Enforcement global de execução
- `executor.py`: Interface obrigatória para execução real
- `metrics.py`: Métricas e monitoramento do Kernel

> Consulte o blueprint para integração com outros módulos do runtime.

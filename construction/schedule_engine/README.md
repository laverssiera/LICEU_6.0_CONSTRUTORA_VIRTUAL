# Schedule Engine

Engine para transformar uma Product Tree em cronograma físico-financeiro.

## Componentes
- `task.py`: Modelo de tarefa
- `convert.py`: Conversão ProductNode → Task
- `dependencies.py`: Regras de dependência
- `scheduler.py`: Cálculo de datas
- `financial.py`: Curva financeira e S-curve
- `event.py`: Geração de evento compatível com o Kernel
- `send_to_kernel.py`: Integração real com o barramento NATS/EventBus

## Exemplo de uso
Veja o arquivo `example.py`.

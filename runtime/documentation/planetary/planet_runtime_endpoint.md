# Planet Runtime Endpoint

Guia rapido para executar o runtime planetario via HTTP no Kernel App.

## Endpoint

- Metodo: POST
- Rota: /planetary/runtime/run
- App: runtime/kernel_app.py

## Payload

```json
{
  "cycles": 2,
  "cycle_interval_seconds": 5
}
```

Regras de validacao:
- cycles: inteiro >= 1
- cycle_interval_seconds: inteiro >= 0

## Exemplo curl

```bash
curl -X POST "http://127.0.0.1:8000/planetary/runtime/run" \
  -H "Content-Type: application/json" \
  -d '{"cycles":2,"cycle_interval_seconds":5}'
```

## Exemplo de resposta 200

```json
{
  "status": "completed",
  "total_cycles": 2,
  "cycle_interval_seconds": 5,
  "operations": [
    {
      "cycle": 1,
      "steps": [
        {"step": "activate", "result": null},
        {"step": "schedule", "result": null},
        {"step": "coordinate", "result": null}
      ]
    },
    {
      "cycle": 2,
      "steps": [
        {"step": "activate", "result": null},
        {"step": "schedule", "result": null},
        {"step": "coordinate", "result": null}
      ]
    }
  ]
}
```

## Erro de validacao

Quando cycles for menor que 1, a API retorna status 422 por validacao de payload.

## Execucao local do kernel

No diretorio raiz do repositorio, execute:

```bash
/home/codespace/.python/current/bin/python runtime/kernel_app.py
```

Servidor padrao:
- Host: 0.0.0.0
- Porta: 8000
- Swagger UI: http://127.0.0.1:8000/docs

## Smoke test rapido

1. Validar que o app subiu e expoe OpenAPI:

```bash
curl -s "http://127.0.0.1:8000/openapi.json" | head -c 200
```

2. Executar o endpoint planetario com 1 ciclo:

```bash
curl -X POST "http://127.0.0.1:8000/planetary/runtime/run" \
  -H "Content-Type: application/json" \
  -d '{"cycles":1,"cycle_interval_seconds":1}'
```

## Troubleshooting

### 1) Porta 8000 ocupada

Sintoma comum:
- Erro de bind ao iniciar o kernel (address already in use).

Como verificar:

```bash
lsof -i :8000
```

Opcao A: finalizar processo que esta usando a porta.

```bash
kill -9 <PID>
```

Opcao B: subir em outra porta.

```bash
/home/codespace/.python/current/bin/python -m uvicorn runtime.kernel_app:app --host 0.0.0.0 --port 8001 --reload
```

### 2) Erro de import path

Sintoma comum:
- ModuleNotFoundError com pacote runtime.

Causa mais frequente:
- Comando executado fora da raiz do repositorio.

Como corrigir:

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL
/home/codespace/.python/current/bin/python runtime/kernel_app.py
```

Alternativa (equivalente, recomendada para desenvolvimento):

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL
/home/codespace/.python/current/bin/python -m uvicorn runtime.kernel_app:app --host 0.0.0.0 --port 8000 --reload
```

### 3) Conflito de ambiente Python

Sintoma comum:
- FastAPI ou Uvicorn nao encontrado, apesar de instalados em outro ambiente.

Causa mais frequente:
- VS Code/terminal usando interpretador diferente do usado nos testes.

Como validar o interpretador ativo:

```bash
which python
/home/codespace/.python/current/bin/python -V
```

Boa pratica para evitar conflito:
- Sempre execute comandos com o binario absoluto:
  /home/codespace/.python/current/bin/python
- Para testes:

```bash
/home/codespace/.python/current/bin/python -m pytest -q tests/test_planet_runtime.py tests/test_planet_runtime_api.py
```

## Checklist de pre-voo (producao)

1. Confirmar que o kernel sobe sem erro e responde em /docs.
2. Executar o smoke test do OpenAPI e validar retorno HTTP 200.
3. Rodar os testes do Planet Runtime e API antes do deploy.
4. Verificar porta alvo e ausencia de conflito com processos ativos.
5. Validar payload de execucao (cycles >= 1 e cycle_interval_seconds >= 0).

## Preflight automatico (script)

Para executar todos os checks principais de uma vez (testes + smoke HTTP):

```bash
./scripts/planet_runtime_preflight.sh
```

Variaveis opcionais:
- PYTHON_BIN: caminho do interpretador Python.
- API_HOST: host para o kernel temporario de teste (padrao 127.0.0.1).
- API_PORT: porta para o kernel temporario de teste (padrao 18080).
- TARGET_PORT: porta de referencia para aviso de conflito operacional (padrao 8000).

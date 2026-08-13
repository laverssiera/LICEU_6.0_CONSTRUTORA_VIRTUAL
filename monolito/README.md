# Template Oficial de Monolito LICEU 6.0

Este template garante padronização, rastreabilidade e integração total ao ecossistema LICEU 6.0.

## Estrutura Recomendada

```
monolito/
├── main.py
├── handlers/
│   └── __init__.py
├── publishers/
│   └── __init__.py
├── config.py
```

## main.py
- Framework: FastAPI
- Endpoint obrigatório: `/health` (GET)
- Startup padronizado: registra handlers e publishers
- Exemplo de execução local:
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

## handlers/
- Centraliza todos os endpoints de negócio
- Função `register_handlers(app)` para registrar rotas

## publishers/
- Inicialização de publishers/eventos
- Função `register_publishers(app)` para setup de integrações/eventos

## config.py
- Centraliza variáveis de ambiente e parâmetros globais
- Exemplo:
  ```python
  import os
  DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
  NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
  TIMEOUT = int(os.getenv("TIMEOUT", "10"))
  ```

## Regras de Ouro
- Todo monolito deve expor `/health` respondendo 200 OK
- Startup deve registrar handlers e publishers
- Configuração centralizada em `config.py`
- Integração com EventBus do SDK (proibido uso direto do NATS)
- Timeout padrão para chamadas externas

## Exemplo de Healthcheck
```python
@app.get("/health")
def healthcheck():
    return {"status": "ok"}
```

## Observações
- Use sempre o EventBus do SDK para publicar/assinar eventos
- Siga o padrão de handlers/publishers para facilitar manutenção
- Consulte o README principal do repositório para detalhes de integração

---

Dúvidas? Consulte a squad de arquitetura ou abra uma issue com a tag `template-monolito`.

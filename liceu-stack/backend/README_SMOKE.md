# Backend Smoke Test

## Requisitos
- Stack subida com Docker Compose na raiz de liceu-stack.
- Servico backend disponivel em http://localhost:8010.

## Opcao 1 - Script shell

```bash
cd /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/liceu-stack/backend
./scripts_smoke_backend.sh
```

Opcional:

```bash
API_BASE=http://localhost:8010 ./scripts_smoke_backend.sh
```

## Opcao 2 - Colecao HTTP
Arquivo: backend_smoke.http

Fluxo:
1. GET /health
2. POST /business/
3. POST /business/{id}/approve

Use em clientes compatíveis com arquivo .http.

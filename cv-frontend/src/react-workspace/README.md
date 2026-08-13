# React Workspace Kanban (Enterprise)

Modulo React institucional para mesa de operacao LICEU 6.0.

Arquivos principais:
- `KanbanBoard.jsx`: shell trading desk (topbar, sidebar, board, john, activity)
- `useEventBus.js`: assinatura websocket central em `/events/ws`
- `eventHandler.js`: reconciliacao de eventos em cards
- `accessControl.js`: controle de visibilidade por role

Uso esperado:
- Importar `KanbanBoard` dentro de uma entrada React existente.
- Garantir `VITE_API_BASE_URL` apontando para o backend FastAPI.

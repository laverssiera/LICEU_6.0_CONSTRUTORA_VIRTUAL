# Exemplo de uso dos endpoints determinísticos de projetos

## Criar Projeto

POST /api/v1/projects/create

```json
{
  "portfolio": "Residencial",
  "program": "Minha Casa Verde",
  "project": "Edifício Aurora",
  "tenant": "liceu",
  "project_type": "PRJ",
  "year": 2026,
  "metadata": {"localizacao": "SP", "orcamento": 1000000}
}
```

---

## Avançar Fase

POST /api/v1/projects/advance-phase

```json
{
  "project_id": "<ID retornado na criação>",
  "actor": "admin",
  "tenant": "liceu"
}
```

---

## Consultar Auditoria

GET /api/v1/projects/audit-log

---

## Consultar Eventos Federados

GET /api/v1/projects/federated-events

---

> Substitua `<ID retornado na criação>` pelo campo `id` do projeto criado.

Esses endpoints garantem persistência, auditoria e propagação federada determinística do ciclo de vida do projeto.

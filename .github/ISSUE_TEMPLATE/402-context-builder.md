---
name: "402 — Context Builder (CRÍTICO)"
about: "Criar contexto único antes da decisão."
labels: epic:john, epic:cefeida, backend, context
---

## Objetivo
Criar contexto único antes da decisão.

## Escopo
- Entrada: evento bruto (ex: { "type": "wall.selected" })
- Saída: contexto enriquecido (ex: { "client": {...}, "project": {...}, "wall_type": "alvenaria", "cost": 120, "execution_time": "2h/m2", "margin": "22%" })
- Alimenta o Kernel.

## Critérios de Aceite
- Contexto enriquecido disponível para decisão.
- Testes de enriquecimento de contexto.

## Dependências
- Issue #401

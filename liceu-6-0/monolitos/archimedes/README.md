# Archimedes (publisher mock)

Modulo publicador de eventos comerciais no ecossistema LICEU 6.0.

## Objetivo

Simular a origem de valor do funil comercial, publicando eventos de lead e fechamento no barramento canonico.

## Eventos publicados

Ao executar `main.py`, o modulo publica em sequencia:

- `lead.created`
- `deal.closed`

Subject de publicacao:

- `liceu.events` (via `sdk.event_bus.EventBus`)

## Estrutura

- `main.py`: script assincrono que publica os eventos de demo

## Requisitos

- Python 3.10+
- SDK compartilhado acessivel em `/shared/core-sdk`
- NATS acessivel em `nats://nats:4222` (ou `NATS_URL`)

## Como executar

Este script foi desenhado para ambiente containerizado com volume do SDK em `/shared/core-sdk`.

Execucao direta:

```bash
python3 main.py
```

## Validacao

1. Deixe um listener ativo (runtime, JuridicoTech ou HubBackoffice).
2. Execute `main.py`.
3. Confirme no listener a chegada de `lead.created` e `deal.closed`.

## Variavel de ambiente

- `NATS_URL`: endpoint do NATS (padrao `nats://nats:4222`)

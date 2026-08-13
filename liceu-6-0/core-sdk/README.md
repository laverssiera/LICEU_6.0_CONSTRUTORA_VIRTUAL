# Core SDK local

SDK compartilhado do LICEU 6.0 para publicacao de eventos canonicos e geracao de artefatos a partir dos contratos Protobuf.

## Objetivo

Centralizar o acesso ao event bus e manter artefatos sincronizados com o CORE-DNA.

## Estrutura

- `sdk/`: implementacao do EventBus
- `scripts/build_dna.sh`: build de artefatos a partir dos protos
- `scripts/publish_boot_event.py`: publica evento `system.boot`
- `scripts/publish_demo_flow.py`: publica fluxo de demo (`lead.created` e `deal.closed`)
- `generated/`: saida de codigo Python, TypeScript e JSON Schema

## Requisitos

- Python 3.10+
- NATS em `nats://localhost:4222` (ou `NATS_PUBLIC_URL`)
- Protos em `../core_dna/` (ou fallback para `../../core_dna/`)

## Build do CORE-DNA

```bash
chmod +x scripts/build_dna.sh
./scripts/build_dna.sh
```

Saida esperada:

- `generated/python/*_pb2.py`
- `generated/typescript/events.ts`
- `generated/jsonschema/events.schema.json`

## Publicar eventos de teste

No diretorio `core-sdk`, execute com `PYTHONPATH` local:

```bash
PYTHONPATH=. python3 scripts/publish_boot_event.py
PYTHONPATH=. python3 scripts/publish_demo_flow.py
```

## Variavel de ambiente

- `NATS_PUBLIC_URL`: endpoint do NATS (padrao `nats://localhost:4222`)

# JuridicoTech (mock listener)

Servico mock do ecossistema LICEU 6.0 responsavel por consumir eventos juridicos no topico canonico `liceu.events`.

## Objetivo

Este componente existe para validar o encadeamento de eventos entre monolitos, com foco no fluxo de contratos e leads.

## Eventos monitorados

O listener filtra e loga apenas eventos com `type`:

- `contract.created`
- `lead.created`

Assinatura no barramento:

- subject NATS: `liceu.events`

## Estrutura

- `mock_listener.py`: consumidor assincrono NATS
- `requirements.txt`: dependencia minima (`nats-py`)

## Requisitos

- Python 3.10+
- NATS disponivel em `nats://localhost:4222` (ou variavel `NATS_URL`)

## Como executar localmente

No diretorio `liceu-6.0/juridicotech`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 mock_listener.py
```

Saida esperada ao iniciar:

```text
[JURIDICOTECH] ouvindo em nats://localhost:4222: liceu.events
```

## Teste rapido (publicando evento)

Com o listener rodando, em outro terminal execute:

```bash
python3 - <<'PY'
import asyncio, json
from nats.aio.client import Client as NATS

async def main():
	nc = NATS()
	await nc.connect("nats://localhost:4222")
	payload = {
		"type": "contract.created",
		"contract_id": "CTR-001",
		"tenant": "demo"
	}
	await nc.publish("liceu.events", json.dumps(payload).encode())
	await nc.flush()
	await nc.close()

asyncio.run(main())
PY
```

No terminal do JuridicoTech, deve aparecer algo como:

```text
JURIDICO RECEBEU: {'type': 'contract.created', 'contract_id': 'CTR-001', 'tenant': 'demo'}
```

## Variaveis de ambiente

- `NATS_URL`: endpoint do NATS (padrao: `nats://localhost:4222`)

## Observacoes

- O servico e um mock para homologacao de fluxo, nao contem regras juridicas de negocio.
- Eventos sem JSON valido sao logados como `raw` para facilitar troubleshooting.

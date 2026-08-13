# HubBackoffice (mock listener)

Servico mock do ecossistema LICEU 6.0 para consumo de eventos financeiros no topico canonico `liceu.events`.

## Objetivo

Validar o fluxo financeiro orientado a eventos, principalmente para fechamento de negocio, pagamentos e assinatura de contrato.

## Eventos monitorados

O listener loga eventos quando `type` for:

- `deal.closed`
- `payment.generated`
- `contract.signed`

Assinatura no barramento:

- subject NATS: `liceu.events`

## Estrutura

- `mock_listener.py`: consumidor assincrono NATS
- `requirements.txt`: dependencia minima (`nats-py`)

## Requisitos

- Python 3.10+
- NATS acessivel em `nats://localhost:4222` (ou `NATS_URL`)

## Como executar localmente

No diretorio do modulo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 mock_listener.py
```

Saida esperada:

```text
[HUBBACKOFFICE] ouvindo em nats://localhost:4222: liceu.events
```

## Teste rapido

Com o listener ativo, publique um evento de teste em outro terminal:

```bash
python3 - <<'PY'
import asyncio, json
from nats.aio.client import Client as NATS

async def main():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    payload = {
        "type": "payment.generated",
        "payment_id": "PAY-001",
        "amount": 150000,
        "tenant": "demo"
    }
    await nc.publish("liceu.events", json.dumps(payload).encode())
    await nc.flush()
    await nc.close()

asyncio.run(main())
PY
```

## Variavel de ambiente

- `NATS_URL`: endpoint do NATS (padrao `nats://localhost:4222`)

## Observacoes

- Este modulo e mock para homologacao de fluxo, sem regras financeiras completas.
- Mensagens invalidas em JSON sao registradas no formato `raw` para troubleshooting.

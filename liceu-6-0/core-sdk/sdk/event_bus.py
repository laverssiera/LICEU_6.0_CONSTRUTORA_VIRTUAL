import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional
from uuid import uuid4

# Validação de eventos padronizados
import pathlib

_EVENTS_PATH = pathlib.Path(__file__).parent.parent.parent / "core_dna" / "event_names.json"
_EVENTS_REGISTRY = None
def _load_events_registry():
    global _EVENTS_REGISTRY
    if _EVENTS_REGISTRY is None:
        try:
            with open(_EVENTS_PATH, "r", encoding="utf-8") as f:
                import json as _json
                data = _json.load(f)
                _EVENTS_REGISTRY = {(e["name"], e["version"]): e["domain"] for e in data["events"]}
        except Exception as exc:
            print(f"[event-bus] Falha ao carregar eventos: {exc}", flush=True)
            _EVENTS_REGISTRY = {}
    return _EVENTS_REGISTRY

# Validação de payload via JSON Schema
    try:
        import jsonschema
    except ImportError:
        errors.append("jsonschema_nao_instalado")
        return errors
    if key in registry:
        schema_path = pathlib.Path(__file__).parent.parent.parent / "core_dna" / f"{key[0]}.{key[1]}.schema.json"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(instance=event["payload"], schema=schema)
            except jsonschema.ValidationError as ve:
                errors.append(f"payload_invalido={ve.message}")
            except Exception as exc:
                errors.append(f"erro_schema={exc}")
        else:
            errors.append(f"schema_nao_encontrado={schema_path.name}")

# Proíbe uso direto do NATS fora deste módulo
import builtins as _builtins
_orig_import = __import__
def _guarded_import(name, *args, **kwargs):
    if name == "nats.aio.client":
        import inspect
        stack = inspect.stack()
        for frame in stack:
            if "event_bus.py" in frame.filename:
                break
        else:
            raise ImportError("Uso direto de NATS proibido. Utilize o EventBus do SDK.")
    return _orig_import(name, *args, **kwargs)
_builtins.__import__ = _guarded_import
from nats.aio.client import Client as NATS
_builtins.__import__ = _orig_import

Handler = Callable[[dict[str, Any]], Awaitable[None]]
InvalidHandler = Callable[[dict[str, Any], list[str]], Awaitable[None]]
CANONICAL_CHANNEL = "liceu.events"
REQUIRED_EVENT_FIELDS = {"id", "type", "version", "source", "timestamp", "payload", "tenant_id"}


def validate_event(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_fields = sorted(REQUIRED_EVENT_FIELDS - set(event))
    if missing_fields:
        errors.append(f"missing_fields={','.join(missing_fields)}")

    if not isinstance(event.get("payload", {}), dict):
        errors.append("payload_not_object")

    # Enforcement: campo tenant_id obrigatório e não vazio
    if not event.get("tenant_id") or not isinstance(event["tenant_id"], str):
        errors.append("tenant_id_invalido_ou_ausente")

    # Enforcement: campo version obrigatório e não vazio
    if not event.get("version") or not isinstance(event["version"], str) or not event["version"].startswith("v"):
        errors.append("version_invalida_ou_ausente")

    # Enforcement: correlation_id obrigatório
    if not event.get("correlation_id"):
        errors.append("correlation_id_ausente")

    # Validação contra registro de eventos
    registry = _load_events_registry()
    key = (event.get("type"), event.get("version"))
    if key not in registry:
        errors.append(f"evento_nao_registrado={key}")
    else:
        domain = registry[key]
        if event.get("domain") and event["domain"] != domain:
            errors.append(f"dominio_invalido={event.get('domain')}")

    return errors


class EventBus:
    def __init__(self, nats_url: Optional[str] = None, channel: str = "liceu.events") -> None:
        if channel != CANONICAL_CHANNEL:
            raise ValueError(f"Canal invalido: {channel}. Use apenas {CANONICAL_CHANNEL}.")

        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://nats:4222")
        self.channel = channel
        self.nc = NATS()

    async def _ensure_connected(self) -> None:
        if not self.nc.is_connected:
            await self.connect()

    async def connect(self) -> None:
        if not self.nc.is_connected:
            await self.nc.connect(self.nats_url)

    async def close(self) -> None:
        if self.nc.is_connected:
            await self.nc.close()

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "unknown",
        version: str = "v1",
    ) -> None:
        await self._ensure_connected()
        event = {
            "id": str(uuid4()),
            "type": event_type,
            "version": version,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        await self.nc.publish(self.channel, json.dumps(event).encode())

    async def publish_dlq(self, event: dict[str, Any], reason: str = "handler_error") -> None:
        dlq_event = {
            "id": str(uuid4()),
            "type": event.get("type", "unknown"),
            "version": event.get("version", "v1"),
            "source": event.get("source", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": event.get("payload", {}),
            "dlq_reason": reason,
        }
        await self._ensure_connected()
        await self.nc.publish("liceu.dlq", json.dumps(dlq_event).encode())

    async def subscribe(self, handler: Handler, invalid_handler: Optional[InvalidHandler] = None) -> None:
        await self._ensure_connected()

        async def cb(msg):
            data = json.loads(msg.data.decode())
            validation_errors = validate_event(data)
            if validation_errors:
                if invalid_handler is not None:
                    await invalid_handler(data, validation_errors)
                else:
                    print(f"[event-bus] evento invalido descartado: {validation_errors}", flush=True)
                return

            await handler(data)

        await self.nc.subscribe(self.channel, cb=cb)

    async def run_forever(self, handler: Handler, invalid_handler: Optional[InvalidHandler] = None) -> None:
        await self.connect()
        await self.subscribe(handler, invalid_handler=invalid_handler)
        while True:
            await asyncio.sleep(60)

    async def subscribe_with_retry(self, handler: Handler, invalid_handler: Optional[InvalidHandler] = None, max_retries: int = 5, base_delay: float = 1.0) -> None:
        await self._ensure_connected()

        async def cb(msg):
            data = json.loads(msg.data.decode())
            validation_errors = validate_event(data)
            if validation_errors:
                if invalid_handler is not None:
                    await invalid_handler(data, validation_errors)
                else:
                    print(f"[event-bus] evento invalido descartado: {validation_errors}", flush=True)
                return

            attempt = 0
            while attempt <= max_retries:
                try:
                    await handler(data)
                    await msg.ack()
                    break
                except Exception as e:
                    attempt += 1
                    delay = base_delay * (2 ** (attempt - 1))
                    print(f"[event-bus] erro handler, retry {attempt}/{max_retries} em {delay:.1f}s: {e}", flush=True)
                    await asyncio.sleep(delay)
            else:
                print(f"[event-bus] evento enviado para DLQ após {max_retries} tentativas.", flush=True)
                await self.publish_dlq(data, reason=f"handler_error_{max_retries}_tentativas")
                await msg.ack()

        await self.nc.subscribe(self.channel, cb=cb, manual_ack=True)

    async def publish_event(self, event_type: str, payload: dict, source: str = "unknown", version: str = "v1", correlation_id: str = None) -> None:
        pipeline_id = payload.get("pipeline_id")
        if not pipeline_id:
            reject_event({"type": event_type, "payload": payload, "reason": "pipeline_id ausente"})
            return
        stage = get_pipeline(pipeline_id)
        if not is_event_allowed(stage, event_type):
            reject_event({"type": event_type, "payload": payload, "stage": stage, "reason": "evento não permitido para o estágio"})
            return
        event = {
            "id": str(uuid4()),
            "type": event_type,
            "version": version,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "correlation_id": correlation_id,
        }
        await self._ensure_connected()
        await self.nc.publish(self.channel, json.dumps(event).encode())

    async def subscribe_event(self, handler: Handler, invalid_handler: Optional[InvalidHandler] = None) -> None:
        await self.subscribe(handler, invalid_handler)

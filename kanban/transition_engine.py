from kanban.pipeline_stages import PipelineStage
from kanban.pipeline_history import log_transition
from liceu-6.0.core-sdk.sdk.event_bus import EventBus
import asyncio
from datetime import datetime, timedelta

# Definição da ordem oficial dos estágios
STAGE_FLOW = [
    PipelineStage.IDEIA,
    PipelineStage.ESTUDO_TECNICO,
    PipelineStage.VIABILIDADE_FINANCEIRA,
    PipelineStage.SWOT,
    PipelineStage.MERCADO,
    PipelineStage.MARKET_SHARE,
    PipelineStage.COMITE,
    PipelineStage.APROVADO,
    PipelineStage.REPROVADO,
    PipelineStage.TERMO_ABERTURA,
    PipelineStage.PILOTO,
    PipelineStage.LICOES,
    PipelineStage.ESCALA,
    PipelineStage.PAYBACK,
    PipelineStage.RETORNO,
    PipelineStage.BUSINESS_CASE,
]

LOCKED_PIPELINES = set()

def lock_pipeline(pipeline_id):
    LOCKED_PIPELINES.add(pipeline_id)

def unlock_pipeline(pipeline_id):
    LOCKED_PIPELINES.discard(pipeline_id)

class InvalidTransition(Exception):
    pass

def validate_transition(current_stage, next_stage):
    try:
        idx = STAGE_FLOW.index(current_stage)
        allowed = STAGE_FLOW[idx + 1]
        if next_stage != allowed:
            raise InvalidTransition(f"Transição inválida: {current_stage} → {next_stage}. Permitido: {allowed}")
    except (ValueError, IndexError):
        raise InvalidTransition(f"Estágio desconhecido ou final: {current_stage}")

async def emit_event(event_type, payload, correlation_id=None):
    bus = EventBus()
    await bus.connect()
    await bus.publish_event(
        event_type=event_type,
        payload=payload,
        source="kanban",
        version="v1",
        correlation_id=correlation_id or payload.get("pipeline_id")
    )

def gatilhos_automaticos(pipeline_id, to_stage):
    # Exemplo: ao atingir TERMO_ABERTURA, dispara eventos para outros domínios
    if to_stage == PipelineStage.TERMO_ABERTURA.value:
        asyncio.run(emit_event("project.created", {"pipeline_id": pipeline_id}, correlation_id=pipeline_id))
        asyncio.run(emit_event("structure.created", {"pipeline_id": pipeline_id}, correlation_id=pipeline_id))
        asyncio.run(emit_event("finance.plan.created", {"pipeline_id": pipeline_id}, correlation_id=pipeline_id))

SLA_DIAS = {
    PipelineStage.ESTUDO_TECNICO.value: 7,
    PipelineStage.VIABILIDADE_FINANCEIRA.value: 5,
    # Adicione outros estágios e SLAs conforme necessário
}

def check_sla(pipeline_id, to_stage):
    # Busca última transição para o estágio
    from kanban.pipeline_history import get_db
    conn = get_db()
    cur = conn.execute("SELECT timestamp FROM pipeline_history WHERE pipeline_id=? AND to_stage=? ORDER BY timestamp DESC LIMIT 1", (pipeline_id, to_stage))
    row = cur.fetchone()
    conn.close()
    if row and to_stage in SLA_DIAS:
        ts = datetime.fromisoformat(row[0])
        limite = ts + timedelta(days=SLA_DIAS[to_stage])
        if datetime.utcnow() > limite:
            print(f"[SLA] Pipeline {pipeline_id} atrasado em {to_stage}")
            asyncio.run(emit_event("pipeline.delayed", {"pipeline_id": pipeline_id, "stage": to_stage}, correlation_id=pipeline_id))

def move_stage(pipeline_id, current_stage, next_stage, actor="system"):
    if pipeline_id in LOCKED_PIPELINES:
        raise Exception(f"Pipeline {pipeline_id} está travado para alteração manual.")
    validate_transition(current_stage, next_stage)
    log_transition(pipeline_id, current_stage.value, next_stage.value, actor)
    print(f"Pipeline {pipeline_id} avançou: {current_stage} → {next_stage}")
    payload = {
        "pipeline_id": pipeline_id,
        "from_stage": current_stage.value,
        "to_stage": next_stage.value,
        "actor": actor
    }
    asyncio.run(emit_event("pipeline.stage.changed", payload, correlation_id=pipeline_id))
    gatilhos_automaticos(pipeline_id, next_stage.value)
    check_sla(pipeline_id, next_stage.value)

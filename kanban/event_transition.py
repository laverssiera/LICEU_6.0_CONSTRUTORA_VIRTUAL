# Transição baseada em eventos canônicos
from kanban.pipeline_stages import PipelineStage
from kanban.transition_engine import move_stage

# Mapeamento de eventos para transições
EVENT_STAGE_MAP = {
    "finance.generated": PipelineStage.VIABILIDADE_FINANCEIRA,
    "committee.approved": PipelineStage.APROVADO,
    "contract.signed": PipelineStage.TERMO_ABERTURA,
    # Adicione outros eventos conforme necessário
}

def handle_event(pipeline_id, current_stage, event_type):
    if event_type in EVENT_STAGE_MAP:
        next_stage = EVENT_STAGE_MAP[event_type]
        move_stage(pipeline_id, current_stage, next_stage)
        print(f"Transição via evento: {event_type} → {next_stage}")
    else:
        print(f"Evento {event_type} não mapeado para transição de estágio.")

# Exemplo de uso
if __name__ == "__main__":
    handle_event("pipeline-1", PipelineStage.ESTUDO_TECNICO, "finance.generated")

# Matriz Stage → Eventos Permitidos
STAGE_EVENT_MATRIX = {
    "IDEIA": ["pipeline.created"],
    "ESTUDO_TECNICO": ["tech.analysis.started", "tech.analysis.completed"],
    "VIABILIDADE_FINANCEIRA": ["finance.generated"],
    "SWOT": ["swot.started", "swot.completed"],
    "MERCADO": ["market.analysis.started", "market.analysis.completed"],
    "MARKET_SHARE": ["market.share.calculated"],
    "COMITE": ["committee.approved", "committee.rejected"],
    "APROVADO": ["contract.signed"],
    "REPROVADO": [],
    "TERMO_ABERTURA": ["project.created"],
    "PILOTO": ["pilot.started", "pilot.completed"],
    "LICOES": ["lessons.learned"],
    "ESCALA": ["scale.started", "scale.completed"],
    "PAYBACK": ["payback.calculated"],
    "RETORNO": ["return.calculated"],
    "BUSINESS_CASE": ["business.case.closed"],
}

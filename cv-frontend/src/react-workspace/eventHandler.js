const KNOWN_STAGES = ['leads', 'negotiation', 'proposal', 'juridico', 'closed'];

function mapStage(eventType, payload) {
  if (typeof payload?.stage === 'string' && KNOWN_STAGES.includes(payload.stage)) {
    return payload.stage;
  }

  const stageMap = {
    'lead.created': 'leads',
    'match.generated': 'negotiation',
    'deal.created': 'negotiation',
    'proposal.sent': 'proposal',
    'contract.created': 'juridico',
    'contract.signed': 'juridico',
    'payment.generated': 'closed',
    'deal.closed': 'closed',
  };

  return stageMap[eventType] || 'leads';
}

function resolveCardId(payload = {}) {
  return payload.id || payload.deal_id || payload.lead_id || payload.contract_id || payload.project_id;
}

export function handleEvent(event, setCards, setActivityLog) {
  const eventType = String(event?.type || event?.event_type || '').toLowerCase().trim();
  const payload = event?.payload && typeof event.payload === 'object' ? event.payload : {};
  const id = resolveCardId(payload);

  if (!eventType || !id) return;

  setCards((previous) => {
    const exists = previous.find((item) => String(item.id) === String(id));
    const nextStage = mapStage(eventType, payload);

    if (!exists) {
      return [
        {
          id,
          title: payload.title || payload.name || `Card ${id}`,
          entity_type: payload.entity_type || 'entity',
          owner_id: payload.owner_id || payload.owner || null,
          risk: payload.risk || 'unknown',
          value: payload.value || payload.amount || 0,
          stage: nextStage,
        },
        ...previous,
      ];
    }

    return previous.map((item) => {
      if (String(item.id) !== String(id)) return item;
      return {
        ...item,
        stage: nextStage,
        title: payload.title || item.title,
        risk: payload.risk || item.risk,
        value: payload.value || payload.amount || item.value,
      };
    });
  });

  setActivityLog((previous) => [
    {
      id: `${Date.now()}-${Math.random()}`,
      ts: new Date().toISOString(),
      eventType,
      cardId: id,
    },
    ...previous,
  ].slice(0, 60));
}

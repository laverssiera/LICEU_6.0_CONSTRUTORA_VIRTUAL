class TemporalMemory:
    async def state_at(self, timestamp):
        """Retorna o estado do ecossistema em um timestamp específico."""
        ...

    async def causal_chain(self, trace_id):
        """Retorna a cadeia causal de um trace_id global."""
        ...

    async def reconstruct_world(self, timestamp):
        """Reconstrói o mundo/ecossistema em um ponto do tempo."""
        ...

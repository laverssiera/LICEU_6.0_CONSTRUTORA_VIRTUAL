class CausalGraph:
    async def link_event(self, source, target):
        """Cria ligação causal entre eventos/source-target."""
        ...

    async def build_chain(self, trace_id):
        """Constrói cadeia causal completa a partir de um trace_id global."""
        ...

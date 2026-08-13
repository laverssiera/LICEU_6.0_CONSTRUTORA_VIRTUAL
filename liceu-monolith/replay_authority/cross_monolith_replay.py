class CrossMonolithReplay:
    async def trace_event(self, trace_id, event):
        """Traça evento globalmente entre Johns e LICEU."""
        ...

    async def replay(self, trace_id):
        """Reproduz cadeia causal global de um evento."""
        ...

class RuntimeRegistry:
    async def register_runtime(self, runtime):
        """Registra um runtime ativo na federação."""
        ...

    async def active_runtimes(self):
        """Retorna lista de runtimes ativos."""
        ...
